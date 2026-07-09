"""
Media module routes.

POST /media/upload is intentionally a server-side proxy upload (not a
client-direct-to-storage signed-upload-URL flow) so every byte is
validated (size + actual magic-byte content type) before it ever
reaches storage. A direct-to-storage flow would mean a malicious client
could upload arbitrary content straight to the bucket, bypassing
validation entirely.

Ownership rule: a user may only upload media attributed to themselves
(owner_id is always the authenticated user's id, never client-supplied)
for STUDENT_ID specifically. Business-scoped purposes (logo, cover,
portfolio) will gain a business-ownership check once the Businesses
module exists; until then they're also scoped to the uploading user.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.modules.auth.models import User, UserRole
from app.modules.media.deps import get_storage
from app.modules.media.schemas import MediaUploadResponse, SignedUrlResponse
from app.modules.media.service import MediaError, MediaService
from app.modules.media.storage import StorageBackend
from app.modules.media.validation import UploadPurpose

settings = get_settings()
router = APIRouter(prefix="/media", tags=["media"])
admin_router = APIRouter(
    prefix="/admin/media",
    tags=["admin", "media"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)

MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    purpose: UploadPurpose = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
) -> MediaUploadResponse:
    # Read with a hard cap slightly above the limit so we reject early
    # rather than buffering an arbitrarily large request body in memory.
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB size limit",
        )

    service = MediaService(storage)
    try:
        storage_key = await service.upload(content=content, purpose=purpose, owner_id=user.id)
    except MediaError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    return MediaUploadResponse(storage_key=storage_key, purpose=purpose)


@admin_router.get("/student-id-url", response_model=SignedUrlResponse)
async def get_student_id_url(
    user_id: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> SignedUrlResponse:
    """
    Admin-only — used during student-ID verification review to view a
    private upload without ever exposing a permanent public URL.

    Takes user_id rather than a raw storage_key: the storage key itself
    never needs to leave the server at all this way, consistent with
    UserPublicResponse never serializing it to regular users either.
    """
    import uuid

    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID") from exc

    user = await db.get(User, uid)
    if user is None or user.student_id_storage_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student ID has been submitted for this user",
        )

    service = MediaService(storage)
    expires_in = 600
    try:
        url = await service.get_private_url(user.student_id_storage_key, expires_in_seconds=expires_in)
    except MediaError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return SignedUrlResponse(url=url, expires_in_seconds=expires_in)
