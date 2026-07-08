"""
Application configuration.

All configuration is sourced from environment variables. No secrets are
ever hardcoded. In production, these are injected by the hosting platform
(Render) via its environment variable management.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "UMATANI"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: PostgresDsn

    # --- Security / JWT ---
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- Argon2id parameters (tuned for server-side hashing cost) ---
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST_KB: int = 65536  # 64 MB
    ARGON2_PARALLELISM: int = 2

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Email verification ---
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "no-reply@umatani.app"

    # --- Object storage (abstracted; Supabase Storage default impl) ---
    STORAGE_BACKEND: Literal["supabase", "local"] = "supabase"
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None
    SUPABASE_STORAGE_BUCKET: str = "umatani-media"

    # --- Rate limiting ---
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "5/minute"

    # --- File upload limits ---
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_MIME_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_DOCUMENT_MIME_TYPES: list[str] = ["application/pdf"]

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def secret_key_must_not_be_default(cls, v: str) -> str:
        insecure_defaults = {"secret", "changeme", "your-secret-key", ""}
        if v.lower() in insecure_defaults:
            raise ValueError("JWT_SECRET_KEY must be set to a secure random value")
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — avoids re-parsing env on every request."""
    return Settings()  # type: ignore[call-arg]
