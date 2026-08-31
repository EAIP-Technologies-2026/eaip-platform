"""Goal domain models — BusinessGoal, Objective, KpiDefinition, GoalProgress, GoalConfig."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class GoalStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MeasurementType(StrEnum):
    COUNT = "count"
    DURATION = "duration"
    PERCENTAGE = "percentage"
    BINARY = "binary"


class KpiDirection(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class ObjectiveStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class KpiDefinition(BaseModel):
    """Definition of a Key Performance Indicator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    unit: str = ""
    target_value: float = 0.0
    current_value: float = 0.0
    measurement_type: MeasurementType = MeasurementType.COUNT
    direction: KpiDirection = KpiDirection.HIGHER_IS_BETTER
    met_threshold: float = 1.0


class Objective(BaseModel):
    """A decomposable sub-goal within a BusinessGoal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    goal_id: str
    name: str
    description: str = ""
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    kpis: tuple[KpiDefinition, ...] = Field(default_factory=tuple)
    target_value: float = 0.0
    current_value: float = 0.0
    assigned_worker_id: str = ""
    deadline: datetime | None = None


class BusinessGoal(BaseModel):
    """A high-level business goal decomposed into objectives and tracked with KPIs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    status: GoalStatus = GoalStatus.DRAFT
    priority: Priority = Priority.MEDIUM
    owner: str = ""
    kpis: tuple[KpiDefinition, ...] = Field(default_factory=tuple)
    objectives: tuple[Objective, ...] = Field(default_factory=tuple)
    deadline: datetime | None = None
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GoalProgress(BaseModel):
    """Mutable snapshot of goal progress for a given evaluation cycle."""

    goal_id: str
    overall_progress: float = Field(default=0.0, ge=0.0, le=100.0)
    objectives_progress: dict[str, float] = Field(default_factory=dict)
    kpi_values: dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=utc_now)


class GoalConfig(BaseModel):
    """Configuration for the goal evaluation engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_interval_seconds: float = 60.0
    enable_auto_replan: bool = False
    max_objectives: int = 20
    notification_thresholds: dict[str, float] = Field(
        default_factory=lambda: {"warning": 0.7, "critical": 0.9}
    )


__all__ = [
    "BusinessGoal",
    "GoalConfig",
    "GoalProgress",
    "GoalStatus",
    "KpiDefinition",
    "KpiDirection",
    "MeasurementType",
    "Objective",
    "ObjectiveStatus",
    "Priority",
]
