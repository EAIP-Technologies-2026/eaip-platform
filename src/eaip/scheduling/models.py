from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ScheduleKind(StrEnum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    INTERVAL = "interval"
    CRON = "cron"
    DELAYED = "delayed"


class ScheduleStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class ScheduleTargetType(StrEnum):
    MISSION = "mission"
    WORKFLOW = "workflow"
    AGENT_ACTION = "agent_action"


SchedulePriority = Annotated[int, Field(ge=1, le=5)]


class ScheduleTrigger(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ScheduleKind
    cron_expr: str | None = None
    interval_seconds: int | None = None
    run_at: datetime | None = None
    timezone: str = "UTC"


class ExecutionWindow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    start_window: str | None = None
    end_window: str | None = None
    calendar_days: tuple[str, ...] | None = None


class RetryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_retries: int = 3
    delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0


class ScheduleDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    name: str
    description: str = ""
    target_type: ScheduleTargetType
    target_id: str
    trigger: ScheduleTrigger
    execution_window: ExecutionWindow | None = None
    priority: SchedulePriority = 1
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_by: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    schedule_id: str
    tenant_id: str
    status: str = "pending"
    attempt: int = 1
    scheduled_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str = ""
    error: str | None = None


class ScheduleHealth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schedule_id: str
    health_score: float = 1.0
    failure_rate: float = 0.0
    overdue_count: int = 0
    total_executions: int = 0
    failed_executions: int = 0


__all__ = [
    "ExecutionWindow",
    "RetryPolicy",
    "ScheduleDefinition",
    "ScheduleExecution",
    "ScheduleHealth",
    "ScheduleKind",
    "SchedulePriority",
    "ScheduleStatus",
    "ScheduleTargetType",
    "ScheduleTrigger",
]
