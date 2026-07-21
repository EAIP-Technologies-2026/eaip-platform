"""Event sourcing domain models — stored events, event streams, projections, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ProjectionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


class StoredEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    event_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    timestamp: datetime = Field(default_factory=utc_now)
    correlation_id: str = ""
    causation_id: str = ""


class EventStream(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    aggregate_type: str
    aggregate_id: str
    events: tuple[StoredEvent, ...] = Field(default=())
    current_version: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class Projection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    aggregate_types: tuple[str, ...] = Field(default=())
    handler_type: str = ""
    status: ProjectionStatus = ProjectionStatus.ACTIVE
    last_processed_event_id: str = ""
    last_processed_at: datetime | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    batch_size: int = 100
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    enable_checkpointing: bool = True
    checkpoint_interval: int = 10


class EventSourcingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_events_per_aggregate: int = 10_000
    enable_snapshots: bool = True
    snapshot_frequency: int = 100
    retention_days: int = 90
    archive_enabled: bool = False


__all__ = [
    "EventSourcingConfig",
    "EventStream",
    "Projection",
    "ProjectionConfig",
    "ProjectionStatus",
    "StoredEvent",
]
