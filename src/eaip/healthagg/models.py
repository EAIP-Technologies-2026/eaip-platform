"""Domain models for the Health Aggregator."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.health.checks import HealthStatus
from eaip.shared.time import utc_now


class HealthDependency(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_component: str
    target_component: str
    dependency_type: str  # hard / soft / circuit
    optional: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class StatusPageStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class HealthStatusPage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    components: tuple[str, ...] = Field(default=())
    layout: dict[str, Any] = Field(default_factory=dict)
    refresh_interval_seconds: int = 30
    public: bool = False
    status: StatusPageStatus = StatusPageStatus.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    timestamp: datetime = Field(default_factory=utc_now)
    component_statuses: dict[str, HealthStatus] = Field(default_factory=dict)
    overall_status: HealthStatus = HealthStatus.HEALTHY
    dependencies_evaluated: int = 0
    duration_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthAggregationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    aggregation_interval_seconds: int = 60
    dependency_graph_enabled: bool = True
    history_retention_days: int = 30
    max_snapshots: int = 10_000
    enable_status_pages: bool = True


__all__ = [
    "HealthAggregationConfig",
    "HealthDependency",
    "HealthSnapshot",
    "HealthStatusPage",
    "StatusPageStatus",
]
