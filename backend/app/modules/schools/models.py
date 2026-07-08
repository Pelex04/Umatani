import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SchoolStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    email_domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[SchoolStatus] = mapped_column(
        String(20), default=SchoolStatus.PENDING, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
