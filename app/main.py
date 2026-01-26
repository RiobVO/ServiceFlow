from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.errors import (
    http_exception_handler,
    value_error_handler,
    validation_exception_handler,
)
from app.core.health import wait_for_database
from app.database.init_db import init_db
from app.routers.health import router as health_router
from app.routers.users import router as users_router
from app.routers.requests import router as requests_router




app = FastAPI(title=settings.APP_NAME, version="0.1.0")

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные обработчики ошибок
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)

@app.on_event("startup")
def on_startup():
    wait_for_database()
    init_db()

app.include_router(health_router)
app.include_router(users_router)
app.include_router(requests_router)
