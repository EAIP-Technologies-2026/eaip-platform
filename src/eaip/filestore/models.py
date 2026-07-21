"""File storage models — assets, versions, providers, config."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class StorageProvider(BaseModel):
    """A configured storage backend."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: Literal["local", "s3", "gcs", "azure"]
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    default: bool = Field(default=False)


class FileConfig(BaseModel):
    """Configuration for file storage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_upload_size_mb: int = Field(default=100, ge=1, le=10240)
    allowed_types: tuple[str, ...] = Field(default_factory=lambda: ("*/*",))
    storage_provider: str = Field(default="local")
    enable_versioning: bool = Field(default=True)
    max_versions: int = Field(default=10, ge=1, le=1000)
    enable_deduplication: bool = Field(default=True)


class FileAsset(BaseModel):
    """A stored file asset with versioning and metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    original_filename: str
    content_type: str
    size_bytes: int = Field(ge=0)
    storage_path: str
    hash: str = Field(default="")
    version: int = Field(default=1, ge=1)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    status: Literal["active", "archived", "deleted"] = Field(default="active")


class AssetVersion(BaseModel):
    """A specific version of a file asset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    asset_id: str
    version: int = Field(ge=1)
    size_bytes: int = Field(ge=0)
    storage_path: str
    hash: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    change_log: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AssetVersion",
    "FileAsset",
    "FileConfig",
    "StorageProvider",
]
