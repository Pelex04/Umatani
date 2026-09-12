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
    APP_NAME: str = "Umata?"
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
    ALLOWED_ORIGINS: list[str] = [
        "https://umata.site",
        "https://www.umata.site",
        "https://umatani.vercel.app",
    ]

    # --- Email verification ---
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    # Used to build links inside emails (verify-email, dashboard, etc).
    FRONTEND_URL: str = "https://www.umata.site"
    # Brevo's transactional HTTP API — not SMTP. Render (and many hosts)
    # block outbound raw SMTP sockets on free/starter tiers, which broke
    # verification email delivery entirely; the HTTP API rides over normal
    # HTTPS instead, which is never blocked. Get a key at
    # https://app.brevo.com/settings/keys/api
    BREVO_API_KEY: str | None = None
    EMAIL_FROM_ADDRESS: str = "no-reply@umatani.app"
    EMAIL_FROM_NAME: str = "Umata?"

    # --- Reminder cascade / admin digest ---
    # Fixed recipient for the daily admin digest (new users, new
    # businesses, businesses pending >24h). Override via env if needed.
    ADMIN_DIGEST_EMAIL: str = "umatani04@gmail.com"
    # Days between each reminder, and how many reminders before suspension.
    REMINDER_INTERVAL_DAYS: int = 3
    REMINDER_MAX_COUNT: int = 3
    # Shared secret checked by /internal/cron/* — GitHub Actions calls
    # these instead of hitting Brevo directly, since its runner IPs
    # rotate constantly and Brevo's IP-authorization security feature
    # blocks unrecognized ones. Must be set for the cron endpoint to
    # work at all; there's no default on purpose.
    CRON_SECRET: str | None = None

    # --- Object storage (abstracted; Supabase Storage default impl) ---
    STORAGE_BACKEND: Literal["supabase", "local"] = "supabase"
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None
    # Private bucket — student ID photos only. Never served via a direct/
    # public URL, only short-lived signed URLs generated on demand for an
    # admin performing identity review.
    SUPABASE_STORAGE_BUCKET: str = "umatani-media"
    # Public bucket — business logos/covers, portfolio items, review
    # photos. These need to render directly in <img> tags across every
    # business card/listing without a signed-URL round trip per image
    # (which would also break browser/CDN caching, since signed URLs
    # expire). Configure this bucket as PUBLIC in Supabase; keep
    # SUPABASE_STORAGE_BUCKET above PRIVATE.
    SUPABASE_PUBLIC_BUCKET: str = "umatani-public"

    # --- Rate limiting ---
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "5/minute"
    # Reports accept submissions from unauthenticated visitors by design
    # (so anyone can flag a scam even without an account) — that same
    # openness is exactly what makes it a spam target, so it gets a much
    # tighter limit than an authenticated action would need.
    RATE_LIMIT_SUPPORT: str = "5/hour"
    RATE_LIMIT_REVIEWS: str = "10/hour"

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
