"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    app_name: str = "ShortX"
    environment: str = "development"
    debug: bool = True
    base_url: str = "http://localhost:8000"  # used to build short links

    # Database
    database_url: str = "postgresql+psycopg2://shortx:shortx@localhost:5432/shortx"

    # Redis (cache + rate limit + celery broker)
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Auth
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION_super_secret_key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day

    # Rate limiting (per API key / IP)
    rate_limit_per_minute: int = 60
    rate_limit_redirect_per_minute: int = 600

    # Caching
    cache_ttl_seconds: int = 3600

    # Short code generation
    short_code_length: int = 7

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
