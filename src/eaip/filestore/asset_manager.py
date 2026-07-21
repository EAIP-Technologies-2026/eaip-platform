"""AssetManager — upload, download, delete, version, duplicate assets."""

from __future__ import annotations

import hashlib
from typing import Any

from eaip.filestore.exceptions import (
    DuplicateFileError,
    FileNotFoundError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from eaip.filestore.models import AssetVersion, FileAsset, FileConfig
from eaip.shared.time import utc_now


class AssetManager:
    """Manages file assets with versioning, deduplication, and search."""

    def __init__(self, config: FileConfig | None = None) -> None:
        """Initialize with optional config."""
        self._config = config or FileConfig()
        self._assets: dict[str, FileAsset] = {}
        self._versions: dict[str, list[AssetVersion]] = {}

    @property
    def config(self) -> FileConfig:
        """Return the current config."""
        return self._config

    def update_config(self, **kwargs: Any) -> FileConfig:
        """Update config fields."""
        self._config = self._config.model_copy(update=kwargs)
        return self._config

    async def upload(
        self,
        file: bytes,
        name: str,
        tags: tuple[str, ...] | None = None,
        content_type: str = "application/octet-stream",
    ) -> FileAsset:
        """Upload a file and return the created asset."""
        if (
            self._config.allowed_types != ("*/*",)
            and content_type not in self._config.allowed_types
        ):
            raise UnsupportedFileTypeError(
                f"Content type {content_type!r} is not allowed.",
                context={"content_type": content_type, "allowed": list(self._config.allowed_types)},
            )
        max_bytes = self._config.max_upload_size_mb * 1024 * 1024
        if len(file) > max_bytes:
            raise FileTooLargeError(
                f"File size {len(file)} exceeds limit of {max_bytes} bytes.",
                context={"size": len(file), "max_size": max_bytes},
            )
        file_hash = hashlib.sha256(file).hexdigest()
        if self._config.enable_deduplication:
            for asset in self._assets.values():
                if asset.hash == file_hash and asset.status == "active":
                    raise DuplicateFileError(
                        f"File with hash {file_hash!r} already exists as asset {asset.id!r}.",
                        context={"existing_asset_id": asset.id, "hash": file_hash},
                    )
        asset_id = f"asset-{name}-{id(file)}"
        asset = FileAsset(
            id=asset_id,
            name=name,
            original_filename=name,
            content_type=content_type,
            size_bytes=len(file),
            storage_path=f"/storage/{asset_id}/{name}",
            hash=file_hash,
            tags=tags or (),
        )
        self._assets[asset_id] = asset
        first_version = AssetVersion(
            id=f"v1-{asset_id}",
            asset_id=asset_id,
            version=1,
            size_bytes=len(file),
            storage_path=asset.storage_path,
            hash=file_hash,
            change_log="Initial upload.",
        )
        self._versions.setdefault(asset_id, []).append(first_version)
        return asset

    async def download(self, asset_id: str, version: int | None = None) -> bytes:
        """Return file content bytes for an asset."""
        asset = await self.get(asset_id)
        if version is not None:
            versions = self._versions.get(asset_id, [])
            for v in versions:
                if v.version == version:
                    return b"simulated content for " + asset.name.encode()
            raise FileNotFoundError(
                f"Version {version} of asset {asset_id!r} not found.",
                context={"asset_id": asset_id, "version": version},
            )
        return b"simulated content for " + asset.name.encode()

    async def delete(self, asset_id: str) -> FileAsset:
        """Mark an asset as deleted."""
        asset = self._assets.pop(asset_id, None)
        if asset is None:
            raise FileNotFoundError(
                f"Asset {asset_id!r} not found.",
                context={"asset_id": asset_id},
            )
        return asset.model_copy(update={"status": "deleted", "updated_at": utc_now()})

    async def get(self, asset_id: str) -> FileAsset:
        """Get an asset by id, raising if not found."""
        asset = self._assets.get(asset_id)
        if asset is None:
            raise FileNotFoundError(
                f"Asset {asset_id!r} not found.",
                context={"asset_id": asset_id},
            )
        return asset

    def list_items(
        self,
        folder: str | None = None,
        tags: tuple[str, ...] | None = None,
    ) -> list[FileAsset]:
        """List assets, optionally filtered by folder path prefix or tags."""
        results = list(self._assets.values())
        if folder:
            results = [a for a in results if a.storage_path.startswith(folder)]
        if tags:
            results = [a for a in results if any(t in a.tags for t in tags)]
        return results

    async def search(self, query: str) -> list[FileAsset]:
        """Search assets by name or original_filename."""
        q = query.lower()
        return [
            a
            for a in self._assets.values()
            if q in a.name.lower() or q in a.original_filename.lower()
        ]

    async def create_version(
        self,
        asset_id: str,
        file: bytes,
        change_log: str = "",
    ) -> AssetVersion:
        """Create a new version of an asset."""
        asset = await self.get(asset_id)
        if not self._config.enable_versioning:
            raise FileTooLargeError(
                "Versioning is disabled.",
                context={"asset_id": asset_id},
            )
        versions = self._versions.setdefault(asset_id, [])
        if len(versions) >= self._config.max_versions:
            raise FileTooLargeError(
                f"Max versions ({self._config.max_versions}) reached for asset {asset_id!r}.",
                context={"asset_id": asset_id, "max_versions": self._config.max_versions},
            )
        new_version_num = asset.version + 1
        file_hash = hashlib.sha256(file).hexdigest()
        version = AssetVersion(
            id=f"v{new_version_num}-{asset_id}",
            asset_id=asset_id,
            version=new_version_num,
            size_bytes=len(file),
            storage_path=asset.storage_path,
            hash=file_hash,
            change_log=change_log,
        )
        versions.append(version)
        updated_asset = asset.model_copy(
            update={
                "version": new_version_num,
                "size_bytes": len(file),
                "hash": file_hash,
                "updated_at": utc_now(),
            }
        )
        self._assets[asset_id] = updated_asset
        return version

    async def get_versions(self, asset_id: str) -> list[AssetVersion]:
        """Return all versions of an asset."""
        await self.get(asset_id)
        return list(self._versions.get(asset_id, []))

    async def get_latest_version(self, asset_id: str) -> AssetVersion:
        """Return the latest version of an asset."""
        versions = await self.get_versions(asset_id)
        if not versions:
            raise FileNotFoundError(
                f"No versions found for asset {asset_id!r}.",
                context={"asset_id": asset_id},
            )
        return versions[-1]

    async def duplicate(self, asset_id: str) -> FileAsset:
        """Duplicate an existing asset."""
        original = await self.get(asset_id)
        new_id = f"dup-{asset_id}-{id(asset_id)}"
        new_asset = original.model_copy(
            update={
                "id": new_id,
                "name": f"{original.name} (copy)",
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        self._assets[new_id] = new_asset
        return new_asset


__all__ = ["AssetManager"]
