from pydantic import BaseModel

from app.modules.media.validation import UploadPurpose


class MediaUploadResponse(BaseModel):
    storage_key: str
    purpose: UploadPurpose


class SignedUrlResponse(BaseModel):
    url: str
    expires_in_seconds: int
