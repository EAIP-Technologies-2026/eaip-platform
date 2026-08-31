"""Data models for platform health — snapshots, metrics, dashboards, and alerts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class HealthSnapshot(BaseModel):
    """A snapshot of component health at a point in time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    component: str
    status: str
    metrics: dict[str, float] = Field(default_factory=dict)
    captured_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthMetric(BaseModel):
    """A single health metric measurement."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    value: float
    unit: str = Field(default="")
    threshold: float | None = Field(default=None)
    breached: bool = Field(default=False)
    recorded_at: datetime = Field(default_factory=utc_now)


class HealthDashboard(BaseModel):
    """A dashboard definition for displaying health metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    components: tuple[str, ...] = Field(default=())
    metrics: tuple[str, ...] = Field(default=())
    refresh_interval_seconds: int = Field(default=30, ge=0)
    is_active: bool = Field(default=True)


class HealthAlert(BaseModel):
    """An alert triggered by a health metric threshold breach."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    metric_name: str
    component: str
    value: float
    threshold: float
    severity: str = Field(default="warning")
    message: str = Field(default="")
    triggered_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None)
    resolved: bool = Field(default=False)


__all__ = [
    "HealthAlert",
    "HealthDashboard",
    "HealthMetric",
    "HealthSnapshot",
]
