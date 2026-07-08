"""
Auth module models.

Design notes:
- Student IDs are stored as a reference (e.g. object-storage key to a
  privately-stored scan) rather than inline, and are never exposed via
  any public-facing schema — only admins reviewing verification requests
  can access them, via a signed, short-lived URL generated on demand.
- RefreshToken stores only a hash of the token plus its jti, so a leaked
  database does not directly yield usable tokens, and individual sessions
  can be revoked.
"""
import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(StrEnum):
    VISITOR = "visitor"  # not persisted as a row; reserved for RBAC checks
    BUSINESS_OWNER = "business_owner"
    ADMIN = "admin"


class UserStatus(StrEnum):
    PENDING_EMAIL_VERIFICATION = "pending_email_verification"
    PENDING_ID_REVIEW = "pending_id_review"  # email confirmed, ID submitted, awaiting admin
    VERIFIED = "verified"
    SUSPENDED = "suspended"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        String(30), default=UserRole.BUSINESS_OWNER, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        String(40), default=UserStatus.PENDING_EMAIL_VERIFICATION, nullable=False
    )
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id", ondelete="RESTRICT"), nullable=True
    )

    # Private — never serialized in any public/owner-facing response schema.
    student_id_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    """
    Stores a hash of each issued refresh token, keyed by jti, so tokens
    can be looked up for rotation/revocation without storing them in
    plaintext (defense-in-depth in case of a database compromise).
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class EmailVerificationToken(Base):
    """
    Single-use token emailed to the user's school address. Stored hashed
    for the same reason as refresh tokens.
    """

    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
