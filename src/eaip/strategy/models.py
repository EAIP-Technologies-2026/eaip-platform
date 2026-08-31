"""Strategic domain models — objectives, initiatives, constraints, themes, state, milestones, risks, KPIs."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ObjectiveStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class InitiativeStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ConstraintSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MilestoneStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"


class RiskLikelihood(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskImpact(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KPITrend(StrEnum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StrategicObjective(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: ObjectiveStatus = ObjectiveStatus.DRAFT
    owner: str = ""
    time_horizon: str = "annual"
    created_at: datetime = Field(default_factory=utc_now)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    supersedes: str | None = None


class StrategicInitiative(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    objective_id: str
    title: str
    description: str = ""
    status: InitiativeStatus = InitiativeStatus.PLANNED
    budget: float = 0.0
    owner: str = ""
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    milestones: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)


class StrategicConstraint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    type: str
    description: str = ""
    severity: ConstraintSeverity = ConstraintSeverity.MEDIUM
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class StrategicTheme(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    name: str
    description: str = ""
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class StrategicState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    version: int = 1
    objectives_snapshot: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    rationale: str = ""
    approval: str = ""
    effective_date: datetime = Field(default_factory=utc_now)
    supersedes: str | None = None


class StrategicMilestone(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    initiative_id: str
    title: str
    target_date: datetime | None = None
    status: MilestoneStatus = MilestoneStatus.PENDING
    owner: str = ""


class StrategicRisk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    objective_id: str
    description: str = ""
    likelihood: RiskLikelihood = RiskLikelihood.MEDIUM
    impact: RiskImpact = RiskImpact.MEDIUM
    mitigation: str = ""


class StrategicKPI(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    objective_id: str
    name: str
    target: float = 0.0
    current: float = 0.0
    trend: KPITrend = KPITrend.STABLE


__all__ = [
    "ConstraintSeverity",
    "InitiativeStatus",
    "KPITrend",
    "MilestoneStatus",
    "ObjectiveStatus",
    "Priority",
    "RiskImpact",
    "RiskLikelihood",
    "StrategicConstraint",
    "StrategicInitiative",
    "StrategicKPI",
    "StrategicMilestone",
    "StrategicObjective",
    "StrategicRisk",
    "StrategicState",
    "StrategicTheme",
]
