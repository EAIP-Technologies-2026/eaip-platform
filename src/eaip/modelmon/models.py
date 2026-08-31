"""Data models for model monitoring — metrics, drift reports, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DriftMetric(StrEnum):
    """Types of drift that can be detected."""

    DATA = "data"
    CONCEPT = "concept"
    MODEL = "model"
    PREDICTION = "prediction"


class ModelMetrics(BaseModel):
    """Performance metrics recorded for a model version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    version: str
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    precision: float = Field(default=0.0, ge=0.0, le=1.0)
    recall: float = Field(default=0.0, ge=0.0, le=1.0)
    f1_score: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    sample_count: int = Field(default=0, ge=0)
    recorded_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DriftReport(BaseModel):
    """A report detailing detected drift for a model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    version: str
    drift_metric: DriftMetric
    drift_score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    is_drifted: bool
    detected_at: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = Field(default_factory=dict)


class MonitorConfig(BaseModel):
    """Configuration for the model monitor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    drift_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    evaluation_interval_seconds: int = Field(default=3600, ge=60)
    max_metrics_history: int = Field(default=1000, ge=1)
    alert_on_drift: bool = Field(default=True)
    alert_on_degradation: bool = Field(default=True)
    degradation_threshold: float = Field(default=0.05, ge=0.0, le=1.0)


__all__ = [
    "DriftMetric",
    "DriftReport",
    "ModelMetrics",
    "MonitorConfig",
]
