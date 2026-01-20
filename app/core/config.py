from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # ✅ вот это лечит твою ошибку
    )

    APP_NAME: str = "Service Request System"

    # === ONLY POSTGRES, NO SQLITE ===
    DATABASE_URL_POSTGRES: str

    # === SECURITY ===
    API_KEY: str
    ADMIN_BOOTSTRAP_KEY: str
    API_KEY_HEADER: str = "X-API-Key"

    @property
    def db_url(self) -> str:
        return self.DATABASE_URL_POSTGRES


settings = Settings()