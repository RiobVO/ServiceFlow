"""HTTP-middleware.

RequestContextMiddleware:
    - Присваивает/пробрасывает X-Request-ID (принимает от клиента, если валиден).
    - Пишет access-лог: method, path, status_code, duration_ms, client_ip.
    - Хранит request_id в contextvars, чтобы structlog подхватывал его
      во всех вложенных логах (сервисы, SQLAlchemy и т.п.).
"""

from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import get_logger, request_id_ctx

REQUEST_ID_HEADER = "X-Request-ID"
_MAX_REQUEST_ID_LEN = 128

# Политика безопасности по умолчанию — минимальная поверхность атаки.
# CSP подходит под API-only сервис (никакого HTML). Если фронт отдаётся
# отсюда же, CSP нужно расширить отдельно.
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}

_log = get_logger("http")


def _normalize_request_id(value: str | None) -> str:
    """Принимаем клиентский X-Request-ID, если он разумной длины; иначе генерируем."""
    if value and 0 < len(value) <= _MAX_REQUEST_ID_LEN and value.isprintable():
        return value
    return uuid.uuid4().hex


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _normalize_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = request_id_ctx.set(request_id)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            # Хендлер Exception напишет Problem Details; здесь — лог access с 500.
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            client_ip = request.client.host if request.client else None
            _log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                query=request.url.query or None,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=request.headers.get("user-agent"),
            )
            # Пишем request_id в ответ, даже если обработчик его не выставил.
            try:
                response_headers = response.headers  # type: ignore[name-defined]
                response_headers[REQUEST_ID_HEADER] = request_id
            except Exception:
                pass
            request_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Проставляет безопасные заголовки на каждый ответ.

    HSTS добавляется только в проде и только поверх HTTPS — иначе
    это бесполезно или мешает разработке.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for name, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if settings.is_prod and request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )
        return response
