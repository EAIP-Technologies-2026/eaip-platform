"""File store domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class FileStoreEvent(DomainEvent):
    """Base event for all file store events."""

    event_type: ClassVar[str] = "eaip.filestore.event"


class FileUploaded(FileStoreEvent):
    """Published when a file is uploaded."""

    event_type: ClassVar[str] = "eaip.filestore.file.uploaded"
    asset_id: str
    name: str
    content_type: str
    size_bytes: int
    tags: tuple[str, ...] = ()


class FileDownloaded(FileStoreEvent):
    """Published when a file is downloaded."""

    event_type: ClassVar[str] = "eaip.filestore.file.downloaded"
    asset_id: str
    name: str
    version: int = 1


class FileDeleted(FileStoreEvent):
    """Published when a file is deleted."""

    event_type: ClassVar[str] = "eaip.filestore.file.deleted"
    asset_id: str
    name: str


class AssetVersionCreated(FileStoreEvent):
    """Published when a new version of an asset is created."""

    event_type: ClassVar[str] = "eaip.filestore.asset.version_created"
    asset_id: str
    version: int
    size_bytes: int
    change_log: str = ""


class FileConfigUpdated(FileStoreEvent):
    """Published when file storage configuration changes."""

    event_type: ClassVar[str] = "eaip.filestore.config.updated"
    changes: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AssetVersionCreated",
    "FileConfigUpdated",
    "FileDeleted",
    "FileDownloaded",
    "FileStoreEvent",
    "FileUploaded",
]
