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

Student ID images are uploaded to a private path and only ever exposed
via a short-lived signed URL, generated on demand for an admin
performing identity review — never a public/direct URL.
"""
import uuid

from app.core.config import get_settings
from app.modules.media.storage import StorageBackend, StorageError
from app.modules.media.validation import (
    UploadPurpose,
    UploadValidationError,
    validate_upload,
)

settings = get_settings()


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

        key = f"{purpose.value}/{owner_id}/{uuid.uuid4()}.{detected.extension}"

        try:
            await self.storage.upload(key, content, detected.mime_type)
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
        (e.g. AuthService.submit_student_id) before trusting a
        client-supplied storage_key.
        """
        parts = storage_key.split("/")
        if len(parts) != 3:
            return False
        purpose_part, owner_part, _filename = parts
        return purpose_part == expected_purpose.value and owner_part == str(expected_owner_id)

    async def get_private_url(self, storage_key: str, *, expires_in_seconds: int = 600) -> str:
        try:
            return await self.storage.get_signed_url(storage_key, expires_in_seconds)
        except StorageError as exc:
            raise MediaError("Could not generate access link for this file") from exc
