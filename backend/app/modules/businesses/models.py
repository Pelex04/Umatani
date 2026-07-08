"""
Businesses module models.

Three tables:
- Business: the main profile. One business per verified owner (V1
  constraint — a student might run multiple businesses, but that's
  post-V1 complexity).
- Service: what the business offers. Free-text name + optional
  description + optional price range. Not an e-commerce item — just
  a discoverable listing per the spec.
- PortfolioItem: media attached to a business profile. Covers images,
  videos (stored as external links in V1 to avoid transcoding costs),
  documents, and plain external links.

average_rating and review_count are stored denormalized on Business
for fast reads — the discovery feed and search results show these
prominently and must not need a JOIN or subquery to render. They are
updated atomically when a review is written (see reviews module).

contact fields (whatsapp, phone, email, social links) are deliberately
on the Business model rather than in a separate contacts table — the
spec's profile definition lists them as first-class profile fields, and
splitting them out adds complexity for no V1 benefit.
"""
import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BusinessStatus(StrEnum):
    PENDING = "pending"      # submitted, awaiting admin approval
    APPROVED = "approved"    # live and visible to visitors
    SUSPENDED = "suspended"  # hidden, owner notified


class PortfolioItemType(StrEnum):
    IMAGE = "image"
    VIDEO_LINK = "video_link"   # YouTube/Vimeo/etc — no transcoding in V1
    DOCUMENT = "document"
    EXTERNAL_LINK = "external_link"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # one business per owner in V1
        index=True,
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Core identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(280), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Media (storage keys for private objects; public URL for logo/cover
    # is resolved by the frontend via a separate signed-URL call so we
    # never embed expiring URLs in API responses)
    logo_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cover_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Contact information
    whatsapp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Social links
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    twitter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tiktok: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status & availability
    status: Mapped[BusinessStatus] = mapped_column(
        String(20), default=BusinessStatus.PENDING, nullable=False, index=True
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Denormalized rating — updated by the reviews module
    average_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    services: Mapped[list["Service"]] = relationship(
        back_populates="business", cascade="all, delete-orphan", order_by="Service.display_order"
    )
    portfolio_items: Mapped[list["PortfolioItem"]] = relationship(
        back_populates="business",
        cascade="all, delete-orphan",
        order_by="PortfolioItem.display_order",
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    business: Mapped["Business"] = relationship(back_populates="services")


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[PortfolioItemType] = mapped_column(String(20), nullable=False)
    # For IMAGE/DOCUMENT: a storage key. For VIDEO_LINK/EXTERNAL_LINK: a URL.
    storage_key_or_url: Mapped[str] = mapped_column(String(512), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    business: Mapped["Business"] = relationship(back_populates="portfolio_items")
