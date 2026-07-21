"""Data models for batch job scheduling."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class BatchJobStatus(StrEnum):
    """Execution status of a batch job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJob(BaseModel):
    """A scheduled batch processing job."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    job_type: str
    priority: int = Field(default=0, ge=0)
    parameters: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0)
    timeout_seconds: int = Field(default=3600, ge=0)
    schedule_cron: str = Field(default="")
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchJobExecution(BaseModel):
    """A single execution attempt for a batch job."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    job_id: str
    status: BatchJobStatus = Field(default=BatchJobStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    result: dict[str, Any] | None = Field(default=None)
    error: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchJobConfig(BaseModel):
    """Configuration for the batch job scheduler."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_jobs: int = Field(default=10, ge=1)
    default_timeout_seconds: int = Field(default=3600, ge=0)
    default_max_retries: int = Field(default=3, ge=0)
    poll_interval_seconds: int = Field(default=30, ge=1)
    history_retention_days: int = Field(default=30, ge=1)


__all__ = [
    "BatchJob",
    "BatchJobConfig",
    "BatchJobExecution",
    "BatchJobStatus",
]
