from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SwarmStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class CollaborationPattern(StrEnum):
    sequential = "sequential"
    parallel = "parallel"
    debate = "debate"
    handoff = "handoff"
    consensus = "consensus"
    supervisor = "supervisor"


class AutonomyLevel(StrEnum):
    read_only = "READ_ONLY"
    suggest = "SUGGEST"
    approval_required = "APPROVAL_REQUIRED"
    bounded_execute = "BOUNDED_EXECUTE"
    autonomous = "AUTONOMOUS"


class SwarmTask(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    description: str
    assigned_to: str = ""
    fallback_agent: str = ""
    required_capability: str = ""
    risk: str = "low"
    budget: dict[str, Any] = Field(default_factory=dict)
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    expected_output: str = ""
    status: str = "pending"
    result: str = ""
    latency_ms: float = 0.0
    cost: float = 0.0


class SwarmDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    swarm_id: str
    tenant_id: str
    name: str
    coordinator: str = ""
    specialists: tuple[str, ...] = Field(default_factory=tuple)
    pattern: CollaborationPattern = CollaborationPattern.parallel
    autonomy_level: AutonomyLevel = AutonomyLevel.suggest
    tasks: tuple[SwarmTask, ...] = Field(default_factory=tuple)
    consensus_config: dict[str, Any] = Field(default_factory=dict)
    status: SwarmStatus = SwarmStatus.pending
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SwarmExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: str
    swarm_id: str
    tenant_id: str
    status: SwarmStatus = SwarmStatus.running
    task_results: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    aggregated_result: str = ""
    consensus: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
