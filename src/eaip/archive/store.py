"""ArchiveStore — abstract storage backend and concrete implementations."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path


class ArchiveStore(ABC):
    """Abstract base class for archive storage backends."""

    @abstractmethod
    def store(self, record_id: str, data: bytes) -> None:
        """Store data identified by *record_id*."""

    @abstractmethod
    def retrieve(self, record_id: str) -> bytes:
        """Retrieve data previously stored under *record_id*."""

    @abstractmethod
    def delete(self, record_id: str) -> None:
        """Delete data identified by *record_id*."""

    @abstractmethod
    def exists(self, record_id: str) -> bool:
        """Return True if *record_id* exists in the store."""


class LocalArchiveStore(ArchiveStore):
    """Filesystem-based archive storage."""

    def __init__(self, base_path: str) -> None:
        """Initialize the store with a base directory path."""
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, record_id: str) -> Path:
        hashed = hashlib.sha256(record_id.encode("utf-8")).hexdigest()
        return self._base / hashed

    def store(self, record_id: str, data: bytes) -> None:
        """Store data identified by record_id."""
        self._path(record_id).write_bytes(data)

    def retrieve(self, record_id: str) -> bytes:
        """Retrieve data previously stored under record_id."""
        return self._path(record_id).read_bytes()

    def delete(self, record_id: str) -> None:
        """Delete data identified by record_id."""
        self._path(record_id).unlink(missing_ok=True)

    def exists(self, record_id: str) -> bool:
        """Return True if record_id exists in the store."""
        return self._path(record_id).exists()


class S3ArchiveStore(ArchiveStore):
    """S3-compatible archive storage (placeholder implementation)."""

    def __init__(self, bucket: str = "archive", prefix: str = "") -> None:
        """Initialize the S3 store with bucket and prefix."""
        self._bucket = bucket
        self._prefix = prefix

    def store(self, record_id: str, data: bytes) -> None:
        """Store data identified by record_id (not implemented)."""
        raise NotImplementedError("S3ArchiveStore.store is not implemented")

    def retrieve(self, record_id: str) -> bytes:
        """Retrieve data by record_id (not implemented)."""
        raise NotImplementedError("S3ArchiveStore.retrieve is not implemented")

    def delete(self, record_id: str) -> None:
        """Delete data by record_id (not implemented)."""
        raise NotImplementedError("S3ArchiveStore.delete is not implemented")

    def exists(self, record_id: str) -> bool:
        """Check if record_id exists (not implemented)."""
        raise NotImplementedError("S3ArchiveStore.exists is not implemented")


__all__ = [
    "ArchiveStore",
    "LocalArchiveStore",
    "S3ArchiveStore",
]
