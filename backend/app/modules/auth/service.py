"""
Auth service layer.

Security behaviors implemented here:
- School-email domain enforcement: registration email's domain must match
  the chosen school's configured email_domain, otherwise registration is
  rejected before any account is created.
- Account lockout: after 5 consecutive failed login attempts, the account
  is locked for 15 minutes (mitigates credential-stuffing / brute force).
- Email enumeration resistance: login and registration failure messages
  are deliberately generic.
- Refresh token rotation: every refresh issues a new refresh token and
  revokes the old one (rotation), limiting the blast radius of a stolen
  refresh token.
- Verification tokens are single-use and hashed at rest.
"""
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import EmailVerificationToken, User, UserRole, UserStatus
from app.modules.auth.repository import (
    EmailVerificationTokenRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.modules.media.service import MediaService
from app.modules.media.validation import UploadPurpose
from app.modules.schools.models import School, SchoolStatus
from app.shared.audit_service import record_audit_event

settings = get_settings()

LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION_MINUTES = 15


def _as_aware_utc(value: datetime) -> datetime:
    """
    Normalize a datetime to UTC-aware.

    Postgres (production) round-trips timezone-aware datetimes correctly
    for TIMESTAMPTZ columns. SQLite (used in tests) does not preserve
    tzinfo even on columns declared DateTime(timezone=True), returning
    naive datetimes instead. Since all datetimes we store are written in
    UTC, a naive value can be safely assumed to be UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class AuthError(Exception):
    """Base class for auth-flow errors with a safe, user-facing message."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _hash_opaque_token(token: str) -> str:
    """SHA-256 for opaque (non-JWT) tokens — fast lookup hash, not a password."""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.verification_tokens = EmailVerificationTokenRepository(db)

    async def register(
        self, *, email: str, password: str, full_name: str, school_id: uuid.UUID
    ) -> tuple[User, str]:
        email = email.lower().strip()

        school = await self.db.get(School, school_id)
        if school is None or school.status != SchoolStatus.APPROVED or not school.is_active:
            raise AuthError("Selected school is not available for registration")

        domain = email.split("@")[-1]
        if domain.lower() != school.email_domain.lower():
            raise AuthError(
                f"Email must be a valid @{school.email_domain} address for this school"
            )

        existing = await self.users.get_by_email(email)
        if existing is not None:
            # Generic message — do not reveal that the account already exists.
            raise AuthError("Unable to register with the provided details")

        user = await self.users.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.BUSINESS_OWNER,
            status=UserStatus.PENDING_EMAIL_VERIFICATION,
            school_id=school_id,
        )

        raw_token = secrets.token_urlsafe(32)
        await self.verification_tokens.create(
            user_id=user.id,
            token_hash=_hash_opaque_token(raw_token),
            expires_at=datetime.now(UTC)
            + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        )

        await record_audit_event(
            self.db,
            action="user.registered",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            actor_role=user.role,
        )

        # Caller (route layer) is responsible for dispatching the email
        # containing raw_token — service layer never sends email directly,
        # keeping I/O concerns out of business logic.
        return user, raw_token

    async def resend_verification_email(self, email: str) -> tuple[User, str] | None:
        """
        Issues a fresh verification token for an existing, not-yet-verified
        account. Returns None (rather than raising) when there's nothing to
        resend — no account, already verified, or suspended — so the route
        layer can give a generic response either way and avoid confirming
        or denying whether a given email is registered.
        """
        email = email.lower().strip()
        user = await self.users.get_by_email(email)
        if user is None or user.status != UserStatus.PENDING_EMAIL_VERIFICATION:
            return None

        raw_token = secrets.token_urlsafe(32)
        await self.verification_tokens.create(
            user_id=user.id,
            token_hash=_hash_opaque_token(raw_token),
            expires_at=datetime.now(UTC)
            + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        )
        return user, raw_token

    async def verify_email(self, raw_token: str) -> User:
        token_hash = _hash_opaque_token(raw_token)

        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.used_at.is_(None),
            )
        )
        token_record = result.scalar_one_or_none()

        if token_record is None:
            # The token might exist but already be used — a very common,
            # entirely legitimate cause is email security scanners (mobile
            # carriers, Outlook/Gmail safe-links, corporate proxies)
            # pre-fetching links in the email to scan them before the
            # person ever clicks, silently burning the one-time token. If
            # that's what happened, the owning account already progressed
            # past email verification — so the person's actual click
            # should succeed, not fail with a confusing "invalid token"
            # for a link they never used yet. Anything else (token never
            # existed, or exists but its owner never verified) stays a
            # hard error.
            stale = await self.db.execute(
                select(EmailVerificationToken).where(
                    EmailVerificationToken.token_hash == token_hash,
                    EmailVerificationToken.used_at.is_not(None),
                )
            )
            stale_record = stale.scalar_one_or_none()
            if stale_record is not None:
                owner = await self.db.get(User, stale_record.user_id)
                if owner is not None and owner.status != UserStatus.PENDING_EMAIL_VERIFICATION:
                    return owner
            raise AuthError("Invalid or expired verification token")

        if _as_aware_utc(token_record.expires_at) < datetime.now(UTC):
            raise AuthError("Invalid or expired verification token")

        user = await self.db.get(User, token_record.user_id)
        if user is None:
            raise AuthError("Invalid or expired verification token")

        token_record.used_at = datetime.now(UTC)
        user.status = UserStatus.PENDING_ID_REVIEW

        await record_audit_event(
            self.db,
            action="user.email_verified",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            actor_role=user.role,
        )
        await self.db.flush()
        return user

    async def submit_student_id(self, user: User, storage_key: str) -> User:
        if user.status != UserStatus.PENDING_ID_REVIEW:
            raise AuthError(
                "Student ID can only be submitted after email verification "
                "and before admin review"
            )

        if not MediaService.verify_key_ownership(
            storage_key, expected_purpose=UploadPurpose.STUDENT_ID, expected_owner_id=user.id
        ):
            raise AuthError("Invalid storage reference for student ID")

        user.student_id_storage_key = storage_key
        await record_audit_event(
            self.db,
            action="user.student_id_submitted",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            actor_role=user.role,
            metadata={"note": "storage key intentionally omitted from audit metadata"},
        )
        await self.db.flush()
        return user

    async def login(self, *, email: str, password: str) -> tuple[User, str, str]:
        email = email.lower().strip()
        user = await self.users.get_by_email(email)

        generic_error = AuthError("Incorrect email or password")

        if user is None:
            raise generic_error

        if user.locked_until and _as_aware_utc(user.locked_until) > datetime.now(UTC):
            raise AuthError(
                "Account temporarily locked due to repeated failed login attempts. "
                "Try again later."
            )

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = datetime.now(UTC) + timedelta(
                    minutes=LOCKOUT_DURATION_MINUTES
                )
                user.failed_login_attempts = 0
            await self.db.flush()
            raise generic_error

        if user.status == UserStatus.SUSPENDED:
            raise AuthError("This account has been suspended")

        # Successful login — reset lockout counters.
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.db.flush()

        access_token = create_access_token(str(user.id), user.role)
        refresh_token, jti = create_refresh_token(str(user.id), user.role)

        await self.refresh_tokens.create(
            jti=jti,
            token_hash=_hash_opaque_token(refresh_token),
            user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        await record_audit_event(
            self.db,
            action="user.login",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            actor_role=user.role,
        )

        return user, access_token, refresh_token

    async def refresh(self, raw_refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(raw_refresh_token, expected_type=TokenType.REFRESH)
        except InvalidTokenError as exc:
            raise AuthError("Invalid or expired refresh token") from exc

        stored = await self.refresh_tokens.get_by_jti(payload.jti)
        if stored is None or stored.revoked:
            raise AuthError("Invalid or expired refresh token")

        if stored.token_hash != _hash_opaque_token(raw_refresh_token):
            # Should be unreachable given jti uniqueness, but defends against
            # any future change that loosens the jti/token binding.
            raise AuthError("Invalid or expired refresh token")

        if _as_aware_utc(stored.expires_at) < datetime.now(UTC):
            raise AuthError("Invalid or expired refresh token")

        user = await self.db.get(User, stored.user_id)
        if user is None or user.status == UserStatus.SUSPENDED:
            raise AuthError("Invalid or expired refresh token")

        # Rotation: revoke old, issue new.
        stored.revoked = True

        new_access = create_access_token(str(user.id), user.role)
        new_refresh, new_jti = create_refresh_token(str(user.id), user.role)

        await self.refresh_tokens.create(
            jti=new_jti,
            token_hash=_hash_opaque_token(new_refresh),
            user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.db.flush()

        return new_access, new_refresh

    async def logout(self, raw_refresh_token: str) -> None:
        try:
            payload = decode_token(raw_refresh_token, expected_type=TokenType.REFRESH)
        except InvalidTokenError:
            return  # Already invalid — nothing to revoke.

        stored = await self.refresh_tokens.get_by_jti(payload.jti)
        if stored is not None:
            stored.revoked = True
            await self.db.flush()
