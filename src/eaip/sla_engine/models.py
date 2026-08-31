"""SLA domain models — definitions, violations, monitors, policies, and dashboard metrics."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SlaStatus(StrEnum):
    ACTIVE = "active"
    WARNING = "warning"
    BREACHED = "breached"
    PAUSED = "paused"
    COMPLETED = "completed"


class SlaPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    warning_threshold: float = 0.0
    breach_threshold: float = 0.0
    evaluation_interval_seconds: float = 60.0
    max_violations: int = 0
    auto_resolve: bool = True
    notify_on_warning: bool = True
    notify_on_breach: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class SlaDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    target_metric: str = ""
    target_value: float = 0.0
    operator: str = "gte"
    window_seconds: float = 300.0
    policy: SlaPolicy = Field(default_factory=SlaPolicy)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    enabled: bool = True
    version: str = "1.0.0"


class SlaViolation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    definition_id: str
    definition_name: str = ""
    metric: str = ""
    actual_value: float = 0.0
    threshold: float = 0.0
    message: str = ""
    severity: str = "warning"
    timestamp: datetime = Field(default_factory=utc_now)
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    resolved: bool = False
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SlaMonitor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    definition_id: str
    status: SlaStatus = SlaStatus.ACTIVE
    current_value: float = 0.0
    last_evaluated: datetime | None = None
    violation_count: int = 0
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SlaDashboard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_definitions: int = 0
    active_monitors: int = 0
    breached_count: int = 0
    warning_count: int = 0
    total_violations: int = 0
    unresolved_violations: int = 0
    avg_response_time_ms: float = 0.0
    compliance_pct: float = 100.0


__all__ = [
    "SlaDashboard",
    "SlaDefinition",
    "SlaMonitor",
    "SlaPolicy",
    "SlaStatus",
    "SlaViolation",
]
