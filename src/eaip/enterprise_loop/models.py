"""M10 Full Autonomous Enterprise Loop — master enterprise loop models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LoopPhase(str, Enum):
    observe = "observe"
    understand = "understand"
    remember = "remember"
    contextualize = "contextualize"
    detect = "detect"
    predict = "predict"
    reason = "reason"
    decide = "decide"
    govern = "govern"
    plan = "plan"
    simulate = "simulate"
    delegate = "delegate"
    execute = "execute"
    observe_outcome = "observe_outcome"
    verify = "verify"
    learn = "learn"
    improve = "improve"
    propose_strategic_update = "propose_strategic_update"


class AutonomyLevel(str, Enum):
    l0 = "L0"  # human only
    l1 = "L1"  # suggestion
    l2 = "L2"  # supervised
    l3 = "L3"  # governed autonomous
    l4 = "L4"  # fully autonomous within bounds


class LoopStatus(str, Enum):
    pending = "pending"
    running = "running"
    awaiting_approval = "awaiting_approval"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class EnterpriseLoopRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"loop-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    objective: str = ""
    current_phase: LoopPhase = LoopPhase.observe
    status: LoopStatus = LoopStatus.pending
    autonomy_level: AutonomyLevel = AutonomyLevel.l2
    phases_completed: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    gap_analysis: dict[str, Any] = Field(default_factory=dict)
    options: list[dict[str, Any]] = Field(default_factory=list)
    chosen_option: dict[str, Any] | None = None
    governance_check: dict[str, Any] = Field(default_factory=dict)
    simulation_result: dict[str, Any] = Field(default_factory=dict)
    workforce_assignment: dict[str, Any] = Field(default_factory=dict)
    workflow_id: str = ""
    execution_result: dict[str, Any] = Field(default_factory=dict)
    kpi_result: dict[str, Any] = Field(default_factory=dict)
    outcome: dict[str, Any] = Field(default_factory=dict)
    learning: dict[str, Any] = Field(default_factory=dict)
    proof_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ObjectiveLoopRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"obj-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    objective: str
    context: dict[str, Any] = Field(default_factory=dict)
    current_state: dict[str, Any] = Field(default_factory=dict)
    gap: dict[str, Any] = Field(default_factory=dict)
    options: list[dict[str, Any]] = Field(default_factory=list)
    governance: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    kpi: dict[str, Any] = Field(default_factory=dict)
    outcome: dict[str, Any] = Field(default_factory=dict)
    learning: dict[str, Any] = Field(default_factory=dict)
    status: LoopStatus = LoopStatus.pending
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AutonomyCheckResult(BaseModel):
    allowed: bool
    reason: str = ""
    requires_approval: bool = False
    checks: dict[str, Any] = Field(default_factory=dict)


class StrategicCorrection(BaseModel):
    correction_id: str = Field(default_factory=lambda: f"scorr-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    expected: dict[str, Any] = Field(default_factory=dict)
    actual: dict[str, Any] = Field(default_factory=dict)
    cause: str = ""
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str = ""
    governance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
