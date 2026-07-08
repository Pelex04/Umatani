import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def slugify(value: str) -> str:
    """Convert a name to a URL-safe slug: lowercase, hyphens, no special chars."""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:120]


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    icon_url: str | None = None
    display_order: int = Field(default=0, ge=0)


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    icon_url: str | None = None
    display_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class CategoryPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    icon_url: str | None
    display_order: int


class CategoryAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    icon_url: str | None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime
