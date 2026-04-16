"""Инициализация FastAPI-приложения."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.errors import (
    domain_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import DomainError
from app.core.health import wait_for_database
from app.core.logging import configure_logging, get_logger
from app.core.metrics import build_instrumentator
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.tracing import setup_tracing
from app.database.init_db import init_db
from app.database.session import engine
from app.routers.health import router as health_router
from app.routers.requests import router as requests_router
from app.routers.users import router as users_router

configure_logging()
_log = get_logger("startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log.info("app_starting", app_name=settings.APP_NAME)
    wait_for_database()
    init_db()
    _log.info("app_ready")
    yield
    _log.info("app_stopping")


_DESCRIPTION = """
**ServiceFlow** — сервис управления внутренними заявками (helpdesk, HR, IT-поддержка).

### Аутентификация
Все запросы требуют заголовок `X-API-Key: <ключ>`. Исключение — bootstrap
первого администратора (`POST /api/v1/users` + `X-Bootstrap-Key`).

### Формат ошибок
Ошибки возвращаются по RFC 7807 — `application/problem+json`:
`{type, title, status, detail, instance, code, request_id, errors?}`.

### Идентификация запросов
Каждый ответ содержит `X-Request-ID` — используйте его при обращении в поддержку.
"""

_TAGS = [
    {"name": "health", "description": "Проверки работоспособности."},
    {"name": "users", "description": "Управление пользователями и API-ключами."},
    {"name": "requests", "description": "Сервисные заявки и их жизненный цикл."},
]

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description=_DESCRIPTION,
    openapi_tags=_TAGS,
    contact={"name": "ServiceFlow Team", "email": "ops@serviceflow.local"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# Middleware выполняются в обратном порядке регистрации.
# Последним регистрируется RequestContextMiddleware — он внешний, оборачивает всё.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Request-ID",
        "X-Bootstrap-Key",
        "Idempotency-Key",
        "If-Match",
    ],
    expose_headers=["X-Request-ID", "ETag"],
    max_age=600,
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

# slowapi требует, чтобы limiter жил в app.state
app.state.limiter = limiter

# Порядок важен: более специфичные хендлеры регистрируем первыми.
app.add_exception_handler(DomainError, domain_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# /health остаётся на корне — стандартная практика для probes k8s/compose.
app.include_router(health_router)

# Доменные роуты — под /api/v1. Будущая v2 сможет жить параллельно.
from fastapi import APIRouter  # noqa: E402

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(users_router)
api_v1.include_router(requests_router)
app.include_router(api_v1)

# Prometheus /metrics
build_instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# OpenTelemetry (включается, если задан OTEL_EXPORTER_OTLP_ENDPOINT)
setup_tracing(app, engine)
