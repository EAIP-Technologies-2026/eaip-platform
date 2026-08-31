"""Data models for data synchronization — jobs, runs, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SyncType(StrEnum):
    """Supported synchronization strategies."""

    FULL = "full"
    INCREMENTAL = "incremental"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(StrEnum):
    """Execution status of a sync run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ConflictResolution(StrEnum):
    """Conflict resolution strategies for bidirectional sync."""

    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    LAST_WRITE_WINS = "last_write_wins"
    MANUAL = "manual"


class SyncJob(BaseModel):
    """A configured data synchronization job."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source: str
    target: str
    sync_type: SyncType = Field(default=SyncType.FULL)
    schedule_cron: str = Field(default="")
    conflict_resolution: ConflictResolution = Field(default=ConflictResolution.LAST_WRITE_WINS)
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SyncRun(BaseModel):
    """A single execution record of a sync job."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    job_id: str
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    items_synced: int = Field(default=0, ge=0)
    items_failed: int = Field(default=0, ge=0)
    status: SyncStatus = Field(default=SyncStatus.PENDING)
    error_message: str = Field(default="")


class SyncConfig(BaseModel):
    """Configuration for the data synchronization service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_concurrent_jobs: int = Field(default=5, ge=1)
    retry_attempts: int = Field(default=3, ge=0)
    retry_delay_seconds: int = Field(default=60, ge=0)
    notify_on_failure: bool = Field(default=True)


__all__ = [
    "ConflictResolution",
    "SyncConfig",
    "SyncJob",
    "SyncRun",
    "SyncStatus",
    "SyncType",
]
