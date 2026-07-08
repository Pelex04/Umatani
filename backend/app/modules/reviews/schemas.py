import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateRequest(BaseModel):
    business_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=10, max_length=2000)
    service_received: str | None = Field(default=None, max_length=255)
    photo_storage_keys: list[str] = Field(default_factory=list, max_length=5)


class ReviewReplyRequest(BaseModel):
    content: str = Field(min_length=5, max_length=1000)


class ReviewPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    storage_key: str


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
