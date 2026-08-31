"""Orchestration domain models — plan, steps, state machine, risk, budgets.

An orchestration plan is an explicit, inspectable, bounded execution plan
that reuses existing EAIP tools, governance, and execution infrastructure.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PlanStatus(StrEnum):
    """Bounded lifecycle states for an orchestration plan."""

    DRAFT = "draft"
    READY = "ready"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    ROLLED_BACK = "rolled_back"


class StepStatus(StrEnum):
    """Status of an individual plan step."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


class FailureClass(StrEnum):
    """Classification of step failures."""

    TRANSIENT = "transient"
    PERMISSION = "permission"
    VALIDATION = "validation"
    DEPENDENCY = "dependency"
    TIMEOUT = "timeout"
    POLICY = "policy"
    UNKNOWN = "unknown"


class PlanRisk(StrEnum):
    """Cumulative risk classification for a plan."""

    INFORMATIONAL = "informational"
    ACTION = "action"
    DESTRUCTIVE = "destructive"


class OrchestrationStep(BaseModel):
    """A single step in an orchestration plan.

    Every step has explicit metadata including risk, dependencies,
    approval requirements, and rollback information.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    id: str
    description: str
    tool_name: str = ""
    skill_id: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    dependencies: tuple[str, ...] = ()
    risk: PlanRisk = PlanRisk.INFORMATIONAL
    required_permission: str = ""
    approval_required: bool = False
    reversible: bool = False
    rollback_tool: str = ""
    rollback_inputs: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60
    max_retries: int = 1
    retry_count: int = 0
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    error: str = ""
    failure_class: FailureClass = FailureClass.UNKNOWN
    started_at: datetime | None = None
    completed_at: datetime | None = None
    correlation_id: str = ""


class ExecutionBudget(BaseModel):
    """Bounded limits for an orchestration run.

    The model cannot remove these limits. They are enforced server-side.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_steps: int = 20
    max_tool_calls: int = 50
    max_retries: int = 3
    max_execution_seconds: int = 600
    max_concurrent_steps: int = 3
    max_destructive_actions: int = 2
    max_rollbacks: int = 5


class OrchestrationPlan(BaseModel):
    """A governed orchestration plan.

    An explicit, inspectable, bounded execution plan. Once approved,
    the executable plan is integrity-protected. If the plan changes,
    approval is invalidated.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    tenant_id: str
    owner_id: str
    objective: str
    description: str = ""
    status: PlanStatus = PlanStatus.DRAFT
    risk: PlanRisk = PlanRisk.INFORMATIONAL
    steps: tuple[OrchestrationStep, ...] = ()
    current_step_index: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    estimated_risk: PlanRisk = PlanRisk.INFORMATIONAL
    approval_id: str = ""
    approval_required: bool = False
    investigation_id: str = ""
    memory_references: tuple[str, ...] = ()
    correlation_ids: tuple[str, ...] = ()
    budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    tool_calls_used: int = 0
    retries_used: int = 0
    rollbacks_used: int = 0
    result_summary: str = ""
    failure_info: str = ""
    plan_hash: str = ""
    provenance: str = "conductor_orchestration"


class CreatePlanRequest(BaseModel):
    """Request to create a new orchestration plan."""

    model_config = ConfigDict(extra="ignore")

    objective: str
    description: str = ""
    steps: list[dict[str, Any]] = Field(default_factory=list)
    investigation_id: str = ""
    estimated_risk: PlanRisk = PlanRisk.INFORMATIONAL


class PlanCommand(BaseModel):
    """Command to send to an orchestration plan."""

    model_config = ConfigDict(extra="ignore")

    command: str = "execute"
    context: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "CreatePlanRequest",
    "ExecutionBudget",
    "FailureClass",
    "OrchestrationPlan",
    "OrchestrationStep",
    "PlanCommand",
    "PlanRisk",
    "PlanStatus",
    "StepStatus",
]
