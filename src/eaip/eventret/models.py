"""Data models for event retention management — policies, jobs, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RetentionAction(StrEnum):
    """Actions to take when a retention policy is applied."""

    DELETE = "delete"
    ARCHIVE = "archive"
    COMPRESS = "compress"


class RetentionJobStatus(StrEnum):
    """Status of a retention job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RetentionPolicy(BaseModel):
    """A policy defining how long events should be retained."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    event_type_pattern: str = Field(default="*")
    max_age_days: int | None = Field(default=None, ge=1)
    max_count: int | None = Field(default=None, ge=1)
    action: RetentionAction = Field(default=RetentionAction.DELETE)
    enabled: bool = Field(default=True)
    priority: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)


class RetentionJob(BaseModel):
    """A single execution of a retention policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    policy_id: str
    affected_events: int = Field(default=0, ge=0)
    status: RetentionJobStatus = Field(default=RetentionJobStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_message: str = Field(default="")

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is not None and self.completed_at is not None:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class EventRetentionConfig(BaseModel):
    """Configuration for the event retention manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    cleanup_interval_minutes: int = Field(default=60, ge=1)
    max_jobs_history: int = Field(default=100, ge=1)
    default_max_age_days: int = Field(default=90, ge=1)
    dry_run: bool = Field(default=False)


__all__ = [
    "EventRetentionConfig",
    "RetentionAction",
    "RetentionJob",
    "RetentionJobStatus",
    "RetentionPolicy",
]
