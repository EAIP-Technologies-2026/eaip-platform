"""Data models for capacity analysis."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ResourceMetric(BaseModel):
    """A single resource usage metric data point."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    metric_name: str
    value: float
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class CapacityReport(BaseModel):
    """A capacity analysis report for a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    period_start: datetime
    period_end: datetime
    current_usage: float = Field(default=0.0, ge=0.0)
    predicted_usage: float = Field(default=0.0, ge=0.0)
    recommended_capacity: float = Field(default=0.0, ge=0.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=utc_now)


class CapacityConfig(BaseModel):
    """Configuration for the capacity analyzer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    threshold_warning: float = Field(default=80.0, ge=0.0, le=100.0)
    threshold_critical: float = Field(default=95.0, ge=0.0, le=100.0)
    prediction_window_hours: int = Field(default=72, ge=1)
    default_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_metrics_per_resource: int = Field(default=10000, ge=1)


__all__ = [
    "CapacityConfig",
    "CapacityReport",
    "ResourceMetric",
]
