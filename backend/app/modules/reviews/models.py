"""
Reviews module models.

Anti-spam enforced at both DB and service level:
- One review per user per business (unique constraint)
- Business owners cannot review their own business
- Replies are limited to one per review from the business owner

review_photos stores storage keys for optional photos attached to a
review (e.g. before/after haircut). Separate table rather than JSONB
so individual photos can be deleted without replacing the whole array.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    service_received: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    photos: Mapped[list["ReviewPhoto"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )
    reply: Mapped["ReviewReply | None"] = relationship(
        back_populates="review", cascade="all, delete-orphan", uselist=False
    )


class ReviewPhoto(Base):
    __tablename__ = "review_photos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)

    review: Mapped["Review"] = relationship(back_populates="photos")


class ReviewReply(Base):
    """Business owner's reply to a review. One reply per review maximum."""
    __tablename__ = "review_replies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    review: Mapped["Review"] = relationship(back_populates="reply")
