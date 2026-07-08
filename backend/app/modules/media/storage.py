"""
Object storage abstraction.

Per the spec's scalability requirements ("object storage abstraction"),
no module outside of this one should know whether files live in
Supabase Storage, local disk, or anything else. Callers depend only on
the StorageBackend protocol.

Two implementations:
- SupabaseStorageBackend: production, talks to Supabase Storage's REST
  API directly via httpx (no SDK dependency).
- LocalStorageBackend: development/testing — writes to local disk. Also
  used in the test suite so upload tests don't require network access.
"""
import os
from pathlib import Path
from typing import Protocol

import httpx

from app.core.config import get_settings

settings = get_settings()


class StorageError(Exception):
    pass


class StorageBackend(Protocol):
    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        """Upload raw bytes to the given key. Overwrites if the key exists."""
        ...

    async def get_signed_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        """Generate a time-limited URL for accessing a private object."""
        ...

    async def delete(self, key: str) -> None:
        ...


class SupabaseStorageBackend:
    """
    Talks to Supabase Storage's REST API directly. Used in production.

    All objects are uploaded to a single configured bucket and addressed
    by key (e.g. "student-ids/<user_id>/<uuid>.jpg",
    "portfolios/<business_id>/<uuid>.png"). The bucket itself should be
    configured as PRIVATE in Supabase — public access is granted per
    object only via short-lived signed URLs, never via public bucket URLs,
    which matters most for student ID images.
    """

    def __init__(self) -> None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise StorageError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured to use "
                "the Supabase storage backend"
            )
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self._headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_KEY,
        }

    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                content=content,
                headers={**self._headers, "Content-Type": content_type, "x-upsert": "true"},
            )
        if resp.status_code not in (200, 201):
            raise StorageError(f"Upload failed ({resp.status_code}): {resp.text}")

    async def get_signed_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        url = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{key}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={"expiresIn": expires_in_seconds},
                headers=self._headers,
            )
        if resp.status_code != 200:
            raise StorageError(f"Could not generate signed URL ({resp.status_code}): {resp.text}")
        signed_path = resp.json().get("signedURL")
        if not signed_path:
            raise StorageError("Supabase response missing signedURL")
        return f"{self.base_url}/storage/v1{signed_path}"

    async def delete(self, key: str) -> None:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{key}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request("DELETE", url, headers=self._headers)
        if resp.status_code not in (200, 204):
            raise StorageError(f"Delete failed ({resp.status_code}): {resp.text}")


class LocalStorageBackend:
    """
    Development/test storage backend — writes to a local directory.
    Never used in production (STORAGE_BACKEND=local is rejected outside
    of development by the get_storage_backend factory below).
    """

    def __init__(self, base_dir: str = "/tmp/umatani-media") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        # Defense against path traversal even though keys are
        # server-generated, never client-supplied.
        safe_key = key.replace("..", "")
        path = (self.base_dir / safe_key).resolve()
        if not str(path).startswith(str(self.base_dir.resolve())):
            raise StorageError("Invalid storage key")
        return path

    async def upload(self, key: str, content: bytes, content_type: str) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    async def get_signed_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        path = self._path_for(key)
        if not path.exists():
            raise StorageError("Object not found")
        return f"file://{path}"

    async def delete(self, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            os.remove(path)


def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "supabase":
        return SupabaseStorageBackend()
    if settings.ENVIRONMENT == "production":
        raise StorageError("LocalStorageBackend must never be used in production")
    return LocalStorageBackend()
