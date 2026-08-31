"""Data models for feature flags, targeting rules, experiments, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class Operator(StrEnum):
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


class TargetingRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    attribute: str
    operator: Operator
    values: tuple[str, ...]


class FeatureFlag(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    key: str
    description: str = Field(default="")
    enabled: bool = Field(default=False)
    rollout_percentage: int = Field(default=0, ge=0, le=100)
    targeting_rules: tuple[TargetingRule, ...] = Field(default=())
    variants: dict[str, str] = Field(default_factory=dict)
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ExperimentVariant(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    config: dict[str, Any] = Field(default_factory=dict)
    weight: int = Field(default=0, ge=0, le=100)


class Experiment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    feature_key: str
    variants: tuple[ExperimentVariant, ...] = Field(default=())
    traffic_allocation: dict[str, int] = Field(default_factory=dict)
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    metrics: tuple[str, ...] = Field(default=())
    start_at: datetime | None = Field(default=None)
    end_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    experiment_id: str
    variant_id: str
    metric_name: str
    metric_value: float
    sample_size: int = Field(default=0)
    confidence_level: float | None = Field(default=None)
    significance: bool | None = Field(default=None)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeatureConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_flags_per_project: int = Field(default=500)
    enable_experiments: bool = Field(default=True)
    experiment_min_sample_size: int = Field(default=100)
    default_rollout_step: int = Field(default=10)
    cache_ttl_seconds: int = Field(default=300)


__all__ = [
    "Experiment",
    "ExperimentResult",
    "ExperimentStatus",
    "ExperimentVariant",
    "FeatureConfig",
    "FeatureFlag",
    "Operator",
    "TargetingRule",
]
