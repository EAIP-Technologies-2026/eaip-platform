"""Pydantic models for configuration snapshots, restore points, and backup config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SnapshotStatus(StrEnum):
    """Status of a configuration snapshot."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class RestoreStatus(StrEnum):
    """Status of a restore operation."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfigSnapshot(BaseModel):
    """A snapshot of a resource's configuration at a point in time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    config_type: str
    data: dict[str, object] = Field(default_factory=dict)
    checksum: str = ""
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    status: SnapshotStatus = SnapshotStatus.ACTIVE


class RestorePoint(BaseModel):
    """A record of a restore operation from a snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    snapshot_id: str
    restored_at: datetime = Field(default_factory=utc_now)
    restored_by: str
    status: RestoreStatus = RestoreStatus.PENDING


class BackupConfig(BaseModel):
    """Configuration settings for the config backup service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_snapshots_per_resource: int = 10
    enable_compression: bool = False
    storage_backend: str = "memory"
    archive_after_days: int = 30
