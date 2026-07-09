from pydantic import BaseModel

from app.modules.media.validation import UploadPurpose


class MediaUploadResponse(BaseModel):
    storage_key: str
    purpose: UploadPurpose
    # Populated for public-bucket purposes only (everything except
    # student_id) — saves the frontend a second round trip to construct
    # the display URL itself, since it's pure string construction anyway.
    public_url: str | None = None


class SignedUrlResponse(BaseModel):
    url: str
    expires_in_seconds: int
