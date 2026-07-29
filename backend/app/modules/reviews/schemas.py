import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.modules.media.service import public_url_or_none
from app.modules.media.validation import UploadPurpose


class ReviewCreateRequest(BaseModel):
    business_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=10, max_length=2000)
    service_received: str | None = Field(default=None, max_length=255)
    photo_storage_keys: list[str] = Field(default_factory=list, max_length=5)


class ReviewReplyRequest(BaseModel):
    content: str = Field(min_length=5, max_length=1000)


class ReviewPhotoResponse(BaseModel):
    """
    storage_key is excluded from serialization — same reasoning as
    business logo/cover and portfolio items: the frontend needs a URL it
    can actually put in an <img> src, not a raw key it has no way to
    turn into one itself. Review photos live in the public bucket (no
    privacy concern, unlike student IDs), so a plain computed URL is
    fine here, no signed-URL round trip needed.
    """
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    storage_key: str = Field(exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_url(self) -> str | None:
        return public_url_or_none(self.storage_key, purpose=UploadPurpose.REVIEW_PHOTO)


class ReviewReplyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    content: str
    created_at: datetime


class ReviewPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    business_id: uuid.UUID
    reviewer_id: uuid.UUID
    rating: int
    comment: str
    service_received: str | None
    created_at: datetime
    photos: list[ReviewPhotoResponse]
    reply: ReviewReplyResponse | None


class ReviewAdminResponse(ReviewPublicResponse):
    is_flagged: bool
    updated_at: datetime


class PaginatedReviewResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[ReviewPublicResponse]
