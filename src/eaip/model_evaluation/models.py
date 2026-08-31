"""Data models for model evaluation and benchmarking."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EvaluationStatus(StrEnum):
    """Status of an evaluation run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MetricType(StrEnum):
    """Types of evaluation metrics."""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    TOKEN_USAGE = "token_usage"  # noqa: S105
    COST = "cost"
    CUSTOM = "custom"


class BenchmarkStatus(StrEnum):
    """Status of a benchmark run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationMetric(BaseModel):
    """A single evaluation metric measurement."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: MetricType
    value: float
    unit: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationConfig(BaseModel):
    """Configuration for a model evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    model_id: str
    model_version: str = Field(default="")
    dataset_id: str = Field(default="")
    metrics: tuple[MetricType, ...] = Field(default=())
    parameters: dict[str, Any] = Field(default_factory=dict)
    max_samples: int = Field(default=0, ge=0)
    timeout_seconds: int = Field(default=300, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Result of a single model evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    config_id: str
    model_id: str
    model_version: str = Field(default="")
    status: EvaluationStatus
    metrics: tuple[EvaluationMetric, ...] = Field(default=())
    summary: str = Field(default="")
    error_message: str = Field(default="")
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelEvaluation(BaseModel):
    """A model evaluation entity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    config_id: str
    model_id: str
    model_version: str = Field(default="")
    status: EvaluationStatus
    results: tuple[EvaluationResult, ...] = Field(default=())
    current_result: EvaluationResult | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationDataset(BaseModel):
    """A dataset used for model evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    version: str = Field(default="")
    record_count: int = Field(default=0, ge=0)
    schema_: dict[str, Any] = Field(default_factory=dict, alias="schema")
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationRun(BaseModel):
    """A complete evaluation run tracking execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    evaluation_id: str
    status: EvaluationStatus
    result_ids: tuple[str, ...] = Field(default=())
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)
    error_message: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    """Summary statistics for a set of evaluations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    evaluation_ids: tuple[str, ...] = Field(default=())
    total_count: int = Field(default=0, ge=0)
    completed_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    avg_duration_ms: float = Field(default=0.0, ge=0.0)
    metrics_summary: dict[str, float] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkConfig(BaseModel):
    """Configuration for a model benchmark."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    model_ids: tuple[str, ...] = Field(default=())
    dataset_id: str = Field(default="")
    metrics: tuple[MetricType, ...] = Field(default=())
    parameters: dict[str, Any] = Field(default_factory=dict)
    iterations: int = Field(default=1, ge=1)
    timeout_seconds: int = Field(default=600, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkResult(BaseModel):
    """Result of a single model benchmark."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    config_id: str
    model_id: str
    model_version: str = Field(default="")
    status: BenchmarkStatus
    scores: tuple[BenchmarkScore, ...] = Field(default=())
    summary: str = Field(default="")
    error_message: str = Field(default="")
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelBenchmark(BaseModel):
    """A model benchmark entity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    config_id: str
    name: str
    status: BenchmarkStatus
    results: tuple[BenchmarkResult, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkScore(BaseModel):
    """A score within a benchmark result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric: MetricType
    value: float
    unit: str = Field(default="")
    weight: float = Field(default=1.0, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkComparison(BaseModel):
    """Comparison of benchmark results across models."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    benchmark_id: str
    result_ids: tuple[str, ...] = Field(default=())
    scores: dict[str, tuple[BenchmarkScore, ...]] = Field(default_factory=dict)
    ranking: tuple[str, ...] = Field(default=())
    summary: str = Field(default="")
    computed_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelPerformanceProfile(BaseModel):
    """Performance profile summarizing evaluation and benchmark history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    model_version: str = Field(default="")
    avg_metrics: dict[str, float] = Field(default_factory=dict)
    best_metrics: dict[str, float] = Field(default_factory=dict)
    worst_metrics: dict[str, float] = Field(default_factory=dict)
    evaluation_count: int = Field(default=0, ge=0)
    benchmark_count: int = Field(default=0, ge=0)
    last_evaluated_at: datetime | None = Field(default=None)
    profile_updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "BenchmarkComparison",
    "BenchmarkConfig",
    "BenchmarkResult",
    "BenchmarkScore",
    "BenchmarkStatus",
    "EvaluationConfig",
    "EvaluationDataset",
    "EvaluationMetric",
    "EvaluationResult",
    "EvaluationRun",
    "EvaluationStatus",
    "EvaluationSummary",
    "MetricType",
    "ModelBenchmark",
    "ModelEvaluation",
    "ModelPerformanceProfile",
]
