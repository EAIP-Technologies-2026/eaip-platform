"""Pydantic models for change log entries, queries, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now


class ChangeAction(StrEnum):
    """Actions that can be recorded in the change log."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class ChangeEntry(BaseModel):
    """A single recorded change to a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: str
    action: ChangeAction
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    changed_by: str
    changed_at: datetime = Field(default_factory=utc_now)
    correlation_id: CorrelationId | None = None


class ChangeQuery(BaseModel):
    """Filters for querying change log entries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_id: str | None = None
    resource_type: str | None = None
    action: ChangeAction | None = None
    changed_by: str | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
    correlation_id: CorrelationId | None = None
    limit: int = 100
    offset: int = 0


class ChangeLogConfig(BaseModel):
    """Configuration settings for the change log service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    retention_days: int = 90
    max_batch_size: int = 1000
    enable_compression: bool = False
    storage_backend: str = "memory"
