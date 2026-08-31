"""Experiment tracking domain models — experiments, variants, runs, metrics, and reports."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentVariant(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    traffic_percent: float = Field(ge=0.0, le=100.0, default=50.0)
    config: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentMetric(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    higher_is_better: bool = True
    target_value: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentParameter(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: str
    description: str = ""


class ExperimentGroup(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    variants: tuple[str, ...] = Field(default_factory=tuple)
    traffic_percent: float = Field(ge=0.0, le=100.0)


class ExperimentAssignment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    experiment_id: str
    variant_id: str
    entity_id: str
    assigned_at: datetime = Field(default_factory=utc_now)
    context: dict[str, Any] = Field(default_factory=dict)


class ExperimentHypothesis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    description: str
    metric_id: str
    expected_effect: str = ""
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.95)
    tested: bool = False
    accepted: bool | None = None
    p_value: float | None = None


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    min_sample_size: int = 100
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.95)
    max_duration_hours: float = 168.0
    traffic_allocation: float = Field(ge=0.0, le=1.0, default=1.0)
    auto_stop: bool = True
    sequential_testing: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    variant_id: str
    metric_id: str
    mean: float = 0.0
    std_dev: float = 0.0
    sample_size: int = 0
    sum_value: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0


class ExperimentComparison(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    experiment_id: str
    control_variant_id: str
    treatment_variant_id: str
    metric_id: str
    lift: float = 0.0
    p_value: float = 0.0
    significant: bool = False
    confidence_level: float = 0.95
    sample_size_control: int = 0
    sample_size_treatment: int = 0
    computed_at: datetime = Field(default_factory=utc_now)


class ExperimentReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    experiment_id: str
    title: str
    summary: str = ""
    comparisons: tuple[ExperimentComparison, ...] = Field(default_factory=tuple)
    hypotheses: tuple[ExperimentHypothesis, ...] = Field(default_factory=tuple)
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentRun(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    experiment_id: str
    status: ExperimentRunStatus = ExperimentRunStatus.PENDING
    variant_id: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: tuple[ExperimentResult, ...] = Field(default_factory=tuple)
    error_message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentAuditLog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    experiment_id: str
    action: str
    actor: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = Field(default_factory=dict)


class Experiment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: tuple[ExperimentVariant, ...] = Field(default_factory=tuple)
    metrics: tuple[ExperimentMetric, ...] = Field(default_factory=tuple)
    hypothesis: ExperimentHypothesis | None = None
    config: ExperimentConfig = Field(default_factory=ExperimentConfig)
    runs: tuple[ExperimentRun, ...] = Field(default_factory=tuple)
    groups: tuple[ExperimentGroup, ...] = Field(default_factory=tuple)
    parameters: tuple[ExperimentParameter, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Experiment",
    "ExperimentAssignment",
    "ExperimentAuditLog",
    "ExperimentComparison",
    "ExperimentConfig",
    "ExperimentGroup",
    "ExperimentHypothesis",
    "ExperimentMetric",
    "ExperimentParameter",
    "ExperimentReport",
    "ExperimentResult",
    "ExperimentRun",
    "ExperimentRunStatus",
    "ExperimentStatus",
    "ExperimentVariant",
]
