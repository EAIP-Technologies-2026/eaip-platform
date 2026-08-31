"""Object storage provider — MinIO/S3-compatible storage.

Provides upload, download, delete, and presigned URL operations
behind a simple abstraction.
"""

from __future__ import annotations

from typing import Any


class ObjectStorageProvider:
    """Production object storage using MinIO (S3-compatible API).

    Usage::

        storage = ObjectStorageProvider(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket="eaip-assets",
        )
        url = await storage.upload("doc-123.pdf", data, "application/pdf")
    """

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "",
        secret_key: str = "",
        bucket: str = "eaip",
        region: str = "us-east-1",
        secure: bool = False,
    ) -> None:
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._region = region
        self._secure = secure
        self._client: Any = None

    async def _ensure_client(self) -> Any:
        if self._client is None:
            from minio import Minio  # type: ignore[import-not-found]

            self._client = Minio(
                self._endpoint,
                access_key=self._access_key,
                secret_key=self._secret_key,
                secure=self._secure,
            )
            if not await self._bucket_exists():
                self._client.make_bucket(self._bucket)
        return self._client

    async def _bucket_exists(self) -> bool:
        try:
            return self._client.bucket_exists(self._bucket)
        except Exception:
            return False

    async def upload(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload data and return the object URL."""
        client = await self._ensure_client()
        client.put_object(
            self._bucket,
            key,
            data,
            length=len(data),
            content_type=content_type,
        )
        return f"{self._endpoint}/{self._bucket}/{key}"

    async def download(self, key: str) -> bytes:
        """Download data by key."""
        client = await self._ensure_client()
        response = client.get_object(self._bucket, key)
        return response.read()

    async def delete(self, key: str) -> bool:
        """Delete an object. Returns True if successful."""
        client = await self._ensure_client()
        client.remove_object(self._bucket, key)
        return True

    async def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Generate a presigned URL for temporary access."""
        from datetime import timedelta

        client = await self._ensure_client()
        return client.presigned_get_object(
            self._bucket, key, expires=timedelta(seconds=expires_seconds)
        )

    async def exists(self, key: str) -> bool:
        """Check if an object exists."""
        client = await self._ensure_client()
        try:
            client.stat_object(self._bucket, key)
            return True
        except Exception:
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Return storage statistics."""
        return {
            "type": "minio",
            "endpoint": self._endpoint,
            "bucket": self._bucket,
        }


__all__ = ["ObjectStorageProvider"]
