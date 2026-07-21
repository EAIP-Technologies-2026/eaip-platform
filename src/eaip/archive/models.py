"""Archive domain models — configs, records, manifests, policies, and query types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ArchiveConfig(BaseModel):
    """Configuration for the archival subsystem."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    storage_backend: str = "local"
    compression_enabled: bool = True
    retention_days: int = 365
    schedule_cron: str | None = None


class ArchiveRecord(BaseModel):
    """A single archived data record."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    record_id: str
    source_collection: str
    archived_at: datetime = Field(default_factory=utc_now)
    size_bytes: int = 0
    checksum: str = ""
    location: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArchiveManifest(BaseModel):
    """A manifest describing a batch of archived records."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    manifest_id: str
    records: tuple[ArchiveRecord, ...] = Field(default_factory=tuple)
    total_size: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    status: str = "created"


class RetentionPolicy(BaseModel):
    """A policy governing data retention duration and action when limits are exceeded."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    policy_id: str
    name: str
    max_age_days: int = 0
    max_size_bytes: int = 0
    action: str = "delete"
    priority: int = 0


class ArchiveQuery(BaseModel):
    """Query parameters for searching archived records."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    filters: dict[str, Any] = Field(default_factory=dict)
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = 100
    offset: int = 0


class ArchiveResult(BaseModel):
    """Paginated result of an archive query."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    records: tuple[ArchiveRecord, ...] = Field(default_factory=tuple)
    total_count: int = 0
    page: int = 1
    page_size: int = 100


class CleanupReport(BaseModel):
    """Report produced after a cleanup cycle."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    items_removed: int = 0
    bytes_freed: int = 0
    duration_ms: int = 0


__all__ = [
    "ArchiveConfig",
    "ArchiveManifest",
    "ArchiveQuery",
    "ArchiveRecord",
    "ArchiveResult",
    "CleanupReport",
    "RetentionPolicy",
]
