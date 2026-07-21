"""Compensation domain models - status, strategy, actions, plans, and transactions."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CompensationStatus(StrEnum):
    PENDING = "pending"
    COMPENSATING = "compensating"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class CompensationStrategy(StrEnum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BEST_EFFORT = "best_effort"
    FAIL_FAST = "fail_fast"


class CompensationAction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    step_id: str
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompensationScope(StrEnum):
    STEP = "step"
    PLAN = "plan"
    WORKFLOW = "workflow"


class CompensationTransaction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    plan_id: str
    step_id: str
    action: CompensationAction
    status: CompensationStatus = CompensationStatus.PENDING
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    result: str = ""
    error: str | None = None


class CompensationStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    actions: tuple[CompensationAction, ...] = Field(default_factory=tuple)
    status: CompensationStatus = CompensationStatus.PENDING
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    timeout_seconds: float = 30.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompensationPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    workflow_id: str
    workflow_name: str = ""
    steps: tuple[CompensationStep, ...] = Field(default_factory=tuple)
    strategy: CompensationStrategy = CompensationStrategy.SEQUENTIAL
    scope: CompensationScope = CompensationScope.PLAN
    status: CompensationStatus = CompensationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    executed_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompensationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    plan_id: str
    plan_name: str = ""
    status: CompensationStatus
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    duration_ms: float = 0.0
    error: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class CompensationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_strategy: CompensationStrategy = CompensationStrategy.SEQUENTIAL
    default_timeout_seconds: float = 30.0
    max_retries: int = 3
    enable_audit_logging: bool = True
    fail_on_first_error: bool = True


class CompensableWorkflow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    steps: tuple[CompensableStep, ...] = Field(default_factory=tuple)
    compensation_plan_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompensableStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    compensation_action: CompensationAction | None = None
    timeout_seconds: float = 30.0
    critical: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "CompensableStep",
    "CompensableWorkflow",
    "CompensationAction",
    "CompensationConfig",
    "CompensationPlan",
    "CompensationResult",
    "CompensationScope",
    "CompensationStatus",
    "CompensationStep",
    "CompensationStrategy",
    "CompensationTransaction",
]
