"""Job models - definitions, runs, schedules, and configuration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class JobPriority(IntEnum):
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


class JobStatus(StrEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    PAUSED = "paused"


class CronExpression(BaseModel):
    """Cron expression for job scheduling."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    minute: str = "*"
    hour: str = "*"
    day_of_month: str = "*"
    month: str = "*"
    day_of_week: str = "*"

    def to_cron_string(self) -> str:
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month} {self.day_of_week}"

    @staticmethod
    def from_string(expression: str) -> CronExpression:
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression!r}")
        return CronExpression(
            minute=parts[0],
            hour=parts[1],
            day_of_month=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )


class RetryConfig(BaseModel):
    """Retry configuration for failed jobs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_retries: int = 3
    delay_seconds: float = 5.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 300.0


class JobSchedule(BaseModel):
    """Schedule configuration for a recurring job."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cron: CronExpression | None = None
    interval_seconds: float | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    max_runs: int = 0


class JobDefinition(BaseModel):
    """Definition of a scheduled job."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    schedule: JobSchedule | None = None
    retry_config: RetryConfig | None = None
    timeout_seconds: float = 0.0
    priority: JobPriority = JobPriority.NORMAL
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class JobRun(BaseModel):
    """Record of a single job execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    job_id: str
    job_name: str = ""
    status: JobStatus = JobStatus.PENDING
    attempt: int = 0
    progress: float = 0.0
    progress_message: str = ""
    result: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    checkpoint_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    run_id: str = ""


@runtime_checkable
class JobHandler(Protocol):
    """Protocol for job execution handlers."""

    async def execute(self, run: JobRun) -> str: ...

    async def cancel(self, run_id: str) -> None: ...

    async def checkpoint(self, run_id: str, data: dict[str, Any]) -> None: ...


JobCoroutine = Callable[..., Awaitable[None]]
"""Type alias for job coroutine functions."""


__all__ = [
    "CronExpression",
    "JobCoroutine",
    "JobDefinition",
    "JobHandler",
    "JobPriority",
    "JobRun",
    "JobSchedule",
    "JobStatus",
    "RetryConfig",
]
