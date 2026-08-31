"""File Storage & Asset Management — upload, download, versioning, dedup.

Bundle-080 of the EAIP Platform Foundation Milestone.
"""

from __future__ import annotations

from eaip.filestore.asset_manager import AssetManager
from eaip.filestore.events import (
    AssetVersionCreated,
    FileConfigUpdated,
    FileDeleted,
    FileDownloaded,
    FileUploaded,
)
from eaip.filestore.exceptions import (
    DuplicateFileError,
    FileNotFoundError,
    FileStoreError,
    FileTooLargeError,
    StorageProviderError,
    UnsupportedFileTypeError,
)
from eaip.filestore.health import FileStoreHealthCheck
from eaip.filestore.integration import FileStoreRuntimeModule
from eaip.filestore.models import (
    AssetVersion,
    FileAsset,
    FileConfig,
    StorageProvider,
)

__all__ = [
    "AssetManager",
    "AssetVersion",
    "AssetVersionCreated",
    "DuplicateFileError",
    "FileAsset",
    "FileConfig",
    "FileConfigUpdated",
    "FileDeleted",
    "FileDownloaded",
    "FileNotFoundError",
    "FileStoreError",
    "FileStoreHealthCheck",
    "FileStoreRuntimeModule",
    "FileTooLargeError",
    "FileUploaded",
    "StorageProvider",
    "StorageProviderError",
    "UnsupportedFileTypeError",
]
