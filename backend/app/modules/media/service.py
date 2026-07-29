"""
Media service.

Key design decision: storage keys are server-generated and namespaced as
"<purpose>/<owner_id>/<uuid>.<ext>" — never client-supplied. This closes
two gaps:
1. A client can't claim an arbitrary storage_key when later referencing
   an upload (e.g. in /auth/student-id) — the key's embedded owner_id
   and purpose are checked against the calling user and the expected
   purpose before being trusted.
2. Path traversal / key collision attacks are impossible since the path
   segments are controlled identifiers (purpose enum, UUID) rather than
   user input.

Student ID images go to the PRIVATE bucket and are only ever exposed via
a short-lived signed URL, generated on demand for an admin performing
identity review — never a public/direct URL. Every other purpose
(business logo/cover, portfolio items, review photos) goes to the
PUBLIC bucket, since these need to render directly in <img> tags across
business cards and listings without a signed-URL round trip per image.
"""
import uuid

from app.core.config import get_settings
from app.modules.media.storage import StorageBackend, StorageError, get_storage_backend
from app.modules.media.validation import (
    UploadPurpose,
    UploadValidationError,
    optimize_image,
    validate_upload,
)

settings = get_settings()

_PRIVATE_PURPOSES = {UploadPurpose.STUDENT_ID}


def _bucket_for(purpose: UploadPurpose) -> str:
    if purpose in _PRIVATE_PURPOSES:
        return settings.SUPABASE_STORAGE_BUCKET
    return settings.SUPABASE_PUBLIC_BUCKET


class MediaError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MediaService:
    def __init__(self, storage: StorageBackend) -> None:
        self.storage = storage

    def _max_size_for(self, purpose: UploadPurpose) -> int:
        if purpose == UploadPurpose.PORTFOLIO_DOCUMENT:
            return settings.MAX_UPLOAD_SIZE_MB
        return min(settings.MAX_UPLOAD_SIZE_MB, 8)  # images don't need the full document limit

    async def upload(
        self,
        *,
        content: bytes,
        purpose: UploadPurpose,
        owner_id: uuid.UUID,
    ) -> str:
        """Validates and stores a file, returning its storage key."""
        try:
            detected = validate_upload(
                content, purpose=purpose, max_size_mb=self._max_size_for(purpose)
            )
        except UploadValidationError as exc:
            raise MediaError(exc.message) from exc

        # PORTFOLIO_DOCUMENT is the one purpose that can validly be either
        # an image or a PDF — only optimize the actual image case.
        if detected.mime_type != "application/pdf":
            content, detected = optimize_image(content, purpose=purpose)

        key = f"{purpose.value}/{owner_id}/{uuid.uuid4()}.{detected.extension}"

        try:
            await self.storage.upload(
                key, content, detected.mime_type, bucket=_bucket_for(purpose)
            )
        except StorageError as exc:
            raise MediaError("Could not store the uploaded file. Please try again.") from exc

        return key

    @staticmethod
    def verify_key_ownership(
        storage_key: str, *, expected_purpose: UploadPurpose, expected_owner_id: uuid.UUID
    ) -> bool:
        """
        Confirms a storage key was actually issued for this owner and
        purpose, by checking the embedded path segments. Used by callers
        (e.g. AuthService.submit_student_id, BusinessService.update)
        before trusting a client-supplied storage_key.
        """
        parts = storage_key.split("/")
        if len(parts) != 3:
            return False
        purpose_part, owner_part, _filename = parts
        return purpose_part == expected_purpose.value and owner_part == str(expected_owner_id)

    async def get_private_url(self, storage_key: str, *, expires_in_seconds: int = 600) -> str:
        try:
            return await self.storage.get_signed_url(
                storage_key, expires_in_seconds, bucket=settings.SUPABASE_STORAGE_BUCKET
            )
        except StorageError as exc:
            raise MediaError("Could not generate access link for this file") from exc

    def get_public_url(self, storage_key: str, *, purpose: UploadPurpose) -> str:
        """
        Direct, permanent URL for a public-bucket object — no network
        call, safe to build repeatedly (e.g. once per business card in a
        search results page) since it's pure string construction.

        Deliberately refuses STUDENT_ID: that purpose's bucket has no
        public-read policy, so building a "public" URL for it would be
        misleading — callers that need to view a student ID must use
        get_private_url via the admin-only signed-URL endpoint instead.
        """
        if purpose in _PRIVATE_PURPOSES:
            raise MediaError(f"{purpose.value} objects are never public")
        return self.storage.get_public_url(storage_key, bucket=_bucket_for(purpose))


def public_url_or_none(storage_key: str | None, *, purpose: UploadPurpose) -> str | None:
    """
    Builds a public media URL from a stored key, for use in response
    schemas' computed fields. Safe to call even when the storage backend
    can't actually be constructed (e.g. Supabase env vars unset in a
    local/test environment) — falls back to None rather than raising,
    since a missing image shouldn't break the whole response.

    Shared across every module that needs to turn a stored key into a
    display URL (businesses, reviews, ...) rather than each one
    duplicating the same try/except, so a new media type doesn't
    accidentally expose a raw storage key just because nobody thought to
    copy this helper into its schema file too.
    """
    if storage_key is None:
        return None
    try:
        return MediaService(get_storage_backend()).get_public_url(storage_key, purpose=purpose)
    except Exception:
        return None
