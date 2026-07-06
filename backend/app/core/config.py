from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    APP_ENV: str = "dev"
    APP_NAME: str = "Kaya BOS"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = Field(..., description="Postgres async DSN")

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    JWT_AUDIENCE: str = "authenticated"

    REDIS_URL: str = "redis://localhost:6379/0"
    FRONTEND_URLS: str = "http://localhost:3000"
    SENTRY_DSN: str = ""

    @property
    def cors_origins(self) -> List[str]:
        return [u.strip() for u in self.FRONTEND_URLS.split(",") if u.strip()]


@lru_cache
def get_settings() -> Settings:
    # pydantic-settings loads DATABASE_URL from the environment; MyPy cannot see that.
    return Settings()  # type: ignore[call-arg]
