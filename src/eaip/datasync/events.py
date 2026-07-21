"""Domain events for data synchronization."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.datasync.models import SyncType
from eaip.events.event import DomainEvent


class SyncJobCreated(DomainEvent):
    """Emitted when a new sync job is created."""

    event_type: ClassVar[str] = "eaip.datasync.job.created"

    job_id: str
    name: str
    sync_type: SyncType


class SyncStarted(DomainEvent):
    """Emitted when a sync run begins."""

    event_type: ClassVar[str] = "eaip.datasync.sync.started"

    run_id: str
    job_id: str
    started_at: datetime


class SyncCompleted(DomainEvent):
    """Emitted when a sync run completes successfully."""

    event_type: ClassVar[str] = "eaip.datasync.sync.completed"

    run_id: str
    job_id: str
    items_synced: int = Field(default=0)
    items_failed: int = Field(default=0)
    duration_seconds: float = Field(default=0.0)


class SyncFailed(DomainEvent):
    """Emitted when a sync run fails."""

    event_type: ClassVar[str] = "eaip.datasync.sync.failed"

    run_id: str
    job_id: str
    error_message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "SyncCompleted",
    "SyncFailed",
    "SyncJobCreated",
    "SyncStarted",
]
