"""
Schools module schemas.

Two response shapes are deliberately kept separate: SchoolPublicResponse
(what visitors/business owners see — only meaningful for approved,
active schools) and SchoolAdminResponse (includes status/is_active so
admins can review pending or suspended schools). Keeping these distinct
means a future field added for admin review tooling doesn't leak into
the public API by accident.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.schools.models import SchoolStatus


class SchoolCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    country: str = Field(min_length=2, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    email_domain: str = Field(min_length=3, max_length=255)
    logo_url: str | None = None

    @field_validator("email_domain")
    @classmethod
    def normalize_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if v.startswith("@"):
            v = v[1:]
        if "." not in v or " " in v:
            raise ValueError("email_domain must be a valid domain, e.g. 'mubas.ac.mw'")
        return v


class SchoolUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    logo_url: str | None = None
    # email_domain intentionally excluded from general update — changing it
    # would silently invalidate every existing verified business owner's
    # registration basis. Use a dedicated, audited flow if this is ever
    # needed (out of scope for V1).


class SchoolPublicResponse(BaseModel):
    """Visible to visitors browsing schools — no status/moderation fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    country: str
    city: str
    logo_url: str | None


class SchoolAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    country: str
    city: str
    email_domain: str
    logo_url: str | None
    status: SchoolStatus
    is_active: bool
    created_at: datetime
