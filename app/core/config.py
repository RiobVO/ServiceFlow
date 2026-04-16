"""Настройки приложения.

Принципы:
    - Секреты только через SecretStr (не попадают в repr/логи).
    - Жёсткая валидация при старте: длина секретов, формат DATABASE_URL, CORS.
    - Окружение (dev/staging/prod) управляет режимами: HSTS, docs, echo.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = "ServiceFlow"
    ENV: Environment = Environment.DEV

    # === DATABASE ===
    DATABASE_URL_POSTGRES: SecretStr

    # === SECURITY ===
    API_KEY_HEADER: str = "X-API-Key"
    ADMIN_BOOTSTRAP_KEY: SecretStr

    # Разделённые запятой origin'ы: https://app.example.com,https://admin.example.com
    CORS_ORIGINS: str = "http://localhost:5173"

    # === LOGGING ===
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # --- производные / вычисляемые ---

    @property
    def db_url(self) -> str:
        return self.DATABASE_URL_POSTGRES.get_secret_value()

    @property
    def admin_bootstrap_key(self) -> str:
        return self.ADMIN_BOOTSTRAP_KEY.get_secret_value()

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.ENV == Environment.PROD

    @property
    def docs_enabled(self) -> bool:
        # Swagger/OpenAPI скрыты в проде — снижает поверхность атаки и
        # не раскрывает ручки посторонним.
        return self.ENV != Environment.PROD

    # --- валидаторы ---

    @field_validator("ADMIN_BOOTSTRAP_KEY")
    @classmethod
    def _validate_bootstrap_key(cls, v: SecretStr) -> SecretStr:
        raw = v.get_secret_value()
        if len(raw) < 24:
            raise ValueError("ADMIN_BOOTSTRAP_KEY должен быть не короче 24 символов.")
        return v

    @field_validator("DATABASE_URL_POSTGRES")
    @classmethod
    def _validate_db_url(cls, v: SecretStr) -> SecretStr:
        raw = v.get_secret_value()
        if not raw.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL_POSTGRES должен быть PostgreSQL DSN "
                "(postgresql://, postgresql+psycopg://, postgresql+asyncpg://)."
            )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _validate_cors(cls, v: str) -> str:
        # В проде запрещаем дикий wildcard — он несовместим с allow_credentials=True
        # и вообще плохая практика. Валидация запускается до знания ENV,
        # поэтому дополнительная проверка идёт в get_settings().
        return v


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        s = Settings()
        if s.is_prod and "*" in s.cors_origins_list:
            raise ValueError("В prod CORS_ORIGINS не должен содержать '*'.")
        _settings = s
    return _settings


# Обратная совместимость: код ранее обращался к settings как к модульной переменной.
settings = get_settings()
