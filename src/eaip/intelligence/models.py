from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CapabilityCategory(StrEnum):
    agent = "agent"
    workflow = "workflow"
    knowledge = "knowledge"
    memory = "memory"
    scheduling = "scheduling"
    workforce = "workforce"
    integration = "integration"
    decision = "decision"
    cognition = "cognition"
    coordination = "coordination"
    simulation = "simulation"


class CapabilityStatus(StrEnum):
    healthy = "healthy"
    degraded = "degraded"
    unavailable = "unavailable"


class CapabilityRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: str
    name: str
    description: str = ""
    category: CapabilityCategory = CapabilityCategory.agent
    version: str = "1.0.0"
    provider: str = "eaip"
    runtime: str = "local"
    required_permissions: tuple[str, ...] = Field(default_factory=tuple)
    required_resources: tuple[str, ...] = Field(default_factory=tuple)
    supported_input_types: tuple[str, ...] = Field(default_factory=tuple)
    supported_output_types: tuple[str, ...] = Field(default_factory=tuple)
    health: CapabilityStatus = CapabilityStatus.healthy
    availability: float = 1.0
    cost_metadata: dict[str, Any] = Field(default_factory=dict)
    latency_metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "default"
    lifecycle_status: str = "active"
    created_at: datetime = Field(default_factory=utc_now)


class CapabilityHealth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: str
    status: CapabilityStatus
    latency_ms: float = 0
    availability: float = 1.0
    last_check: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = Field(default_factory=dict)


class IntelligenceContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: str
    user_id: str = ""
    actor: str = ""
    goal: str = ""
    task: str = ""
    mission_id: str = ""
    workflow_id: str = ""
    agent_id: str = ""
    memory_refs: tuple[str, ...] = Field(default_factory=tuple)
    knowledge_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    constraints: dict[str, Any] = Field(default_factory=dict)
    permissions: tuple[str, ...] = Field(default_factory=tuple)
    budget: dict[str, Any] = Field(default_factory=dict)
    deadline: datetime | None = None
    risk_level: str = "low"
    approval_state: str = "not_required"
    correlation_id: str = ""
    execution_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class KernelExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: str
    tenant_id: str
    capability_id: str
    context: IntelligenceContext
    status: str = "pending"
    result: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    cost: float = 0
    latency_ms: float = 0
    provenance: dict[str, Any] = Field(default_factory=dict)


class SupervisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str
    tenant_id: str
    agent_id: str
    mission_id: str = ""
    goal: str = ""
    progress: float = 0
    confidence: float = 0
    strategy: str = "direct"
    state: str = "running"
    resource_usage: dict[str, Any] = Field(default_factory=dict)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    escalation: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MemoryLayer(StrEnum):
    working = "working"
    task = "task"
    mission = "mission"
    enterprise = "enterprise"
    historical = "historical"


class MemoryConsistencyReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    report_id: str
    tenant_id: str
    contradictions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    duplicates: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    stale_items: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)


class CognitiveHypothesis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    hypothesis_id: str
    tenant_id: str
    title: str
    evidence: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    confidence: float = 0.5
    reasoning_strategy: str = "direct"
    created_at: datetime = Field(default_factory=utc_now)


class DecisionAlternative(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    expected_outcome: str = ""
    cost: float = 0
    risk: float = 0
    confidence: float = 0.5


class DecisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    decision_id: str
    tenant_id: str
    title: str
    objective: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    alternatives: tuple[DecisionAlternative, ...] = Field(default_factory=tuple)
    criteria: dict[str, float] = Field(default_factory=dict)
    evidence: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    assumptions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    risks: tuple[str, ...] = Field(default_factory=tuple)
    confidence: float = 0.5
    recommendation: str = ""
    approvers: tuple[str, ...] = Field(default_factory=tuple)
    execution_id: str = ""
    owner: str = ""
    status: str = "draft"
    actual_outcome: str = ""
    predicted_outcome: str = ""
    outcome_error: float | None = None
    review_status: str = ""
    reversed: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class CoordinationPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    plan_id: str
    tenant_id: str
    objective: str
    priority: str = "operational"
    assigned_agents: tuple[str, ...] = Field(default_factory=tuple)
    tasks: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    resources: dict[str, Any] = Field(default_factory=dict)
    conflicts: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    status: str = "draft"
    outcome: str = ""
    created_at: datetime = Field(default_factory=utc_now)
