"""
Storage tests split into two classes:
- TestKeyOwnershipVerification: synchronous unit tests (no asyncio mark)
- TestLocalStorageBackend: async tests that actually touch the filesystem
"""
import uuid

import pytest

from app.modules.media.service import MediaService
from app.modules.media.storage import LocalStorageBackend, StorageError
from app.modules.media.validation import UploadPurpose


class TestKeyOwnershipVerification:
    """Pure-sync tests — no async marker needed."""

    def test_valid_key_for_correct_owner_and_purpose(self) -> None:
        owner_id = uuid.uuid4()
        key = f"student_id/{owner_id}/{uuid.uuid4()}.jpg"
        assert MediaService.verify_key_ownership(
            key, expected_purpose=UploadPurpose.STUDENT_ID, expected_owner_id=owner_id
        )

    def test_key_for_different_owner_rejected(self) -> None:
        owner_id = uuid.uuid4()
        other_id = uuid.uuid4()
        key = f"student_id/{other_id}/{uuid.uuid4()}.jpg"
        assert not MediaService.verify_key_ownership(
            key, expected_purpose=UploadPurpose.STUDENT_ID, expected_owner_id=owner_id
        )

    def test_key_with_wrong_purpose_rejected(self) -> None:
        owner_id = uuid.uuid4()
        key = f"business_logo/{owner_id}/{uuid.uuid4()}.jpg"
        assert not MediaService.verify_key_ownership(
            key, expected_purpose=UploadPurpose.STUDENT_ID, expected_owner_id=owner_id
        )

    def test_malformed_key_rejected(self) -> None:
        owner_id = uuid.uuid4()
        assert not MediaService.verify_key_ownership(
            "not-a-real-key",
            expected_purpose=UploadPurpose.STUDENT_ID,
            expected_owner_id=owner_id,
        )

    def test_arbitrary_client_supplied_key_rejected(self) -> None:
        owner_id = uuid.uuid4()
        fabricated = f"student_id/{uuid.uuid4()}/fake.jpg"
        assert not MediaService.verify_key_ownership(
            fabricated, expected_purpose=UploadPurpose.STUDENT_ID, expected_owner_id=owner_id
        )


class TestLocalStorageBackend:
    """Async tests — need the event loop."""

    @pytest.mark.asyncio
    async def test_upload_and_signed_url_round_trip(self, tmp_path) -> None:
        backend = LocalStorageBackend(base_dir=str(tmp_path))
        key = "business_logo/abc/test.png"
        await backend.upload(key, b"fake-image-bytes", "image/png")
        url = await backend.get_signed_url(key)
        assert "test.png" in url

    @pytest.mark.asyncio
    async def test_signed_url_for_missing_object_raises(self, tmp_path) -> None:
        backend = LocalStorageBackend(base_dir=str(tmp_path))
        with pytest.raises(StorageError):
            await backend.get_signed_url("does/not/exist.png")

    @pytest.mark.asyncio
    async def test_path_traversal_key_rejected(self, tmp_path) -> None:
        backend = LocalStorageBackend(base_dir=str(tmp_path))
        with pytest.raises(StorageError):
            await backend.upload("../../etc/passwd", b"malicious", "text/plain")

    @pytest.mark.asyncio
    async def test_delete_removes_object(self, tmp_path) -> None:
        backend = LocalStorageBackend(base_dir=str(tmp_path))
        key = "business_logo/abc/test.png"
        await backend.upload(key, b"fake-image-bytes", "image/png")
        await backend.delete(key)
        with pytest.raises(StorageError):
            await backend.get_signed_url(key)
