"""
Security primitives: password hashing and JWT token handling.

Password hashing uses Argon2id (OWASP-recommended) via argon2-cffi, with
parameters tuned in config.py. JWTs are signed with HS256 using a secret
that is validated at startup to never be a known-insecure default.

Access tokens are short-lived (15 min default) and carry the user's role
for RBAC checks. Refresh tokens are long-lived, opaque to claims beyond
identity, and are expected to be stored hashed in the database so they
can be revoked (see modules/auth/repository.py).
"""
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()

_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST_KB,
    parallelism=settings.ARGON2_PARALLELISM,
)


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    sub: str  # user id
    role: str
    type: TokenType
    jti: str  # unique token id, enables refresh-token revocation
    exp: datetime
    iat: datetime


class InvalidTokenError(Exception):
    pass


def hash_password(plain_password: str) -> str:
    """Hash a password using Argon2id."""
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        # Malformed hash or other backend error — treat as failed verification,
        # never raise, to avoid leaking internal state via error responses.
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Check if a stored hash should be upgraded (e.g. cost params changed)."""
    return _hasher.check_needs_rehash(hashed_password)


def _create_token(
    subject: str,
    role: str,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = TokenPayload(
        sub=subject,
        role=role,
        type=token_type,
        jti=str(uuid.uuid4()),
        iat=now,
        exp=now + expires_delta,
    )
    claims = payload.model_dump(mode="python")
    claims["exp"] = int(payload.exp.timestamp())
    claims["iat"] = int(payload.iat.timestamp())
    return jwt.encode(
        claims,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(subject: str, role: str) -> str:
    return _create_token(
        subject, role, TokenType.ACCESS,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str, role: str) -> tuple[str, str]:
    """
    Returns (token, jti). The caller is responsible for persisting a hash
    of the token (keyed by jti) so it can be looked up and revoked.
    """
    now = datetime.now(UTC)
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    payload = TokenPayload(
        sub=subject,
        role=role,
        type=TokenType.REFRESH,
        jti=jti,
        iat=now,
        exp=now + expires_delta,
    )
    claims = payload.model_dump(mode="python")
    claims["exp"] = int(payload.exp.timestamp())
    claims["iat"] = int(payload.iat.timestamp())
    token = jwt.encode(
        claims,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, jti


def decode_token(token: str, expected_type: TokenType) -> TokenPayload:
    """
    Decode and validate a JWT. Raises InvalidTokenError on any failure —
    expired, malformed, wrong signature, or wrong token type (e.g. trying
    to use a refresh token where an access token is required).
    """
    try:
        raw: dict[str, Any] = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        data = TokenPayload.model_validate(raw)
    except (JWTError, ValueError) as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    if data.type != expected_type:
        raise InvalidTokenError(f"Expected {expected_type} token, got {data.type}")

    return data
