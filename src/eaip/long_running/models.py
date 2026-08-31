"""Long-running workflow domain models - workflow, state, checkpoint, and execution plan."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class WorkflowRecoveryStrategy(StrEnum):
    RESTART = "restart"
    RESUME = "resume"
    SKIP_COMPLETED = "skip_completed"
    ROLLBACK = "rollback"


class WorkflowState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: dict[str, Any] = Field(default_factory=dict)
    step_id: str = ""
    attempt: int = 0
    started_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    error: str | None = None


class WorkflowCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    workflow_id: str
    step_id: str = ""
    snapshot: WorkflowSnapshot
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    state: WorkflowState
    context: dict[str, Any] = Field(default_factory=dict)
    step_results: dict[str, str] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)
    captured_at: datetime = Field(default_factory=utc_now)


class WorkflowPersistenceConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    store_type: str = "memory"
    persist_after_each_step: bool = True
    persist_after_heartbeat: bool = False
    checkpoint_ttl_seconds: float = 86400.0
    max_checkpoints: int = 50
    compression_enabled: bool = False
    encryption_enabled: bool = False


class WorkflowExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str
    steps: tuple[str, ...] = Field(default_factory=tuple)
    recovery_strategy: WorkflowRecoveryStrategy = WorkflowRecoveryStrategy.RESUME
    persistence: WorkflowPersistenceConfig = Field(default_factory=WorkflowPersistenceConfig)
    heartbeat_interval_seconds: float = 30.0
    execution_timeout_seconds: float = 0.0
    max_retries: int = 3
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowContinuationToken(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    token: str
    workflow_id: str
    next_step_id: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None


class LongRunningWorkflow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    state: WorkflowState = Field(default_factory=lambda: WorkflowState(workflow_id=""))
    plan: WorkflowExecutionPlan = Field(
        default_factory=lambda: WorkflowExecutionPlan(workflow_id="")
    )
    checkpoints: tuple[WorkflowCheckpoint, ...] = Field(default_factory=tuple)
    continuation_token: WorkflowContinuationToken | None = None
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "LongRunningWorkflow",
    "WorkflowCheckpoint",
    "WorkflowContinuationToken",
    "WorkflowExecutionPlan",
    "WorkflowPersistenceConfig",
    "WorkflowRecoveryStrategy",
    "WorkflowSnapshot",
    "WorkflowState",
    "WorkflowStatus",
]
