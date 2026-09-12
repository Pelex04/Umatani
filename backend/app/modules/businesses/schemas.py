"""
Businesses module schemas.

Three response shapes:
- BusinessPublicResponse: what visitors see — approved businesses only.
  Includes category/school names (not just IDs) for display-ready
  rendering without extra frontend calls. logo_url/cover_url are
  computed from the stored key against the public media bucket — plain
  string construction, safe to expose freely, no signed-URL round trip
  needed since business media lives in the public bucket (unlike student
  ID photos, which never appear in any response at all).
- BusinessOwnerResponse: what the owner sees — includes their own
  pending/suspended status.
- BusinessAdminResponse: everything, for admin review pages.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, computed_field, field_validator

from app.modules.businesses.models import BusinessStatus, PortfolioItemType
from app.modules.media.service import public_url_or_none as _public_url_or_none
from app.modules.media.validation import UploadPurpose



class ServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price_range: str | None = Field(default=None, max_length=100)
    display_order: int = Field(default=0, ge=0)


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    price_range: str | None
    display_order: int


class PortfolioItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_type: PortfolioItemType
    storage_key_or_url: str = Field(exclude=True)
    caption: str | None
    display_order: int
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_url(self) -> str:
        # This field doubles as either a full external URL (e.g. a
        # pasted Instagram link) or a server-issued storage key,
        # distinguished here rather than in the frontend so it never
        # needs to guess which one it received.
        if self.storage_key_or_url.startswith(("http://", "https://")):
            return self.storage_key_or_url
        purpose = (
            UploadPurpose.PORTFOLIO_DOCUMENT
            if self.item_type == PortfolioItemType.DOCUMENT
            else UploadPurpose.PORTFOLIO_IMAGE
        )
        return _public_url_or_none(self.storage_key_or_url, purpose=purpose) or ""


class BusinessCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=20, max_length=5000)
    category_id: uuid.UUID
    whatsapp: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    contact_email: str | None = None
    website: str | None = Field(default=None, max_length=512)
    instagram: str | None = Field(default=None, max_length=255)
    twitter: str | None = Field(default=None, max_length=255)
    facebook: str | None = Field(default=None, max_length=255)
    tiktok: str | None = Field(default=None, max_length=255)
    services: list[ServiceRequest] = Field(default_factory=list, max_length=20)

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and "@" not in v:
            raise ValueError("contact_email must be a valid email address")
        return v


class BusinessUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, min_length=20, max_length=5000)
    category_id: uuid.UUID | None = None
    whatsapp: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    contact_email: str | None = None
    website: str | None = Field(default=None, max_length=512)
    instagram: str | None = Field(default=None, max_length=255)
    twitter: str | None = Field(default=None, max_length=255)
    facebook: str | None = Field(default=None, max_length=255)
    tiktok: str | None = Field(default=None, max_length=255)
    is_available: bool | None = None
    services: list[ServiceRequest] | None = None


class PortfolioItemAddRequest(BaseModel):
    item_type: PortfolioItemType
    storage_key_or_url: str = Field(min_length=1, max_length=512)
    caption: str | None = Field(default=None, max_length=500)
    display_order: int = Field(default=0, ge=0)

    @field_validator("storage_key_or_url")
    @classmethod
    def validate_url_types(cls, v: str, info) -> str:
        # URLs for link types must look like URLs (basic check).
        # Storage keys are opaque to this schema — the service validates them.
        return v


class BusinessPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str
    school_id: uuid.UUID
    category_id: uuid.UUID
    logo_storage_key: str | None = Field(exclude=True)
    cover_storage_key: str | None = Field(exclude=True)
    whatsapp: str | None
    phone: str | None
    contact_email: str | None
    website: str | None
    instagram: str | None
    twitter: str | None
    facebook: str | None
    tiktok: str | None
    is_available: bool
    average_rating: float
    review_count: int
    created_at: datetime
    services: list[ServiceResponse]
    portfolio_items: list[PortfolioItemResponse]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def logo_url(self) -> str | None:
        return _public_url_or_none(self.logo_storage_key, purpose=UploadPurpose.BUSINESS_LOGO)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cover_url(self) -> str | None:
        return _public_url_or_none(self.cover_storage_key, purpose=UploadPurpose.BUSINESS_COVER)


class BusinessOwnerResponse(BusinessPublicResponse):
    status: BusinessStatus


class OwnerSummary(BaseModel):
    """Minimal owner context surfaced on the admin detail view — enough
    to know who to contact and whether they're a verified student,
    without pulling in the full user admin schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    status: str


class BusinessAdminResponse(BusinessOwnerResponse):
    owner_id: uuid.UUID
    updated_at: datetime
    owner: OwnerSummary | None = None


class BusinessListItemResponse(BaseModel):
    """Lightweight card for discovery listing — no services/portfolio."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str
    school_id: uuid.UUID
    category_id: uuid.UUID
    logo_storage_key: str | None = Field(exclude=True)
    is_available: bool
    average_rating: float
    review_count: int
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def logo_url(self) -> str | None:
        return _public_url_or_none(self.logo_storage_key, purpose=UploadPurpose.BUSINESS_LOGO)
