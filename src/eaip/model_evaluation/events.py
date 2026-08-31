"""Domain events for model evaluation and benchmarking."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class EvaluationCreated(DomainEvent):
    """Emitted when a model evaluation is created."""

    event_type: ClassVar[str] = "eaip.model_evaluation.evaluation.created"

    evaluation_id: str
    model_id: str
    config_id: str


class EvaluationStarted(DomainEvent):
    """Emitted when a model evaluation begins."""

    event_type: ClassVar[str] = "eaip.model_evaluation.evaluation.started"

    evaluation_id: str
    model_id: str
    run_id: str


class EvaluationCompleted(DomainEvent):
    """Emitted when a model evaluation completes successfully."""

    event_type: ClassVar[str] = "eaip.model_evaluation.evaluation.completed"

    evaluation_id: str
    model_id: str
    result_id: str
    metrics_count: int = 0


class EvaluationFailed(DomainEvent):
    """Emitted when a model evaluation fails."""

    event_type: ClassVar[str] = "eaip.model_evaluation.evaluation.failed"

    evaluation_id: str
    model_id: str
    error_message: str


class EvaluationCancelled(DomainEvent):
    """Emitted when a model evaluation is cancelled."""

    event_type: ClassVar[str] = "eaip.model_evaluation.evaluation.cancelled"

    evaluation_id: str
    model_id: str
    reason: str = ""


class MetricRecorded(DomainEvent):
    """Emitted when a metric is recorded during evaluation."""

    event_type: ClassVar[str] = "eaip.model_evaluation.metric.recorded"

    evaluation_id: str
    result_id: str
    metric_name: str
    metric_value: float


class BenchmarkCreated(DomainEvent):
    """Emitted when a benchmark is created."""

    event_type: ClassVar[str] = "eaip.model_evaluation.benchmark.created"

    benchmark_id: str
    config_id: str


class BenchmarkStarted(DomainEvent):
    """Emitted when a benchmark begins."""

    event_type: ClassVar[str] = "eaip.model_evaluation.benchmark.started"

    benchmark_id: str
    model_count: int = 0


class BenchmarkCompleted(DomainEvent):
    """Emitted when a benchmark completes successfully."""

    event_type: ClassVar[str] = "eaip.model_evaluation.benchmark.completed"

    benchmark_id: str
    result_count: int = 0


class BenchmarkFailed(DomainEvent):
    """Emitted when a benchmark fails."""

    event_type: ClassVar[str] = "eaip.model_evaluation.benchmark.failed"

    benchmark_id: str
    error_message: str


class BenchmarkComparisonComputed(DomainEvent):
    """Emitted when a benchmark comparison is computed."""

    event_type: ClassVar[str] = "eaip.model_evaluation.benchmark.comparison_computed"

    comparison_id: str
    benchmark_id: str
    ranked_models: tuple[str, ...]


class EvaluationSummaryGenerated(DomainEvent):
    """Emitted when an evaluation summary is generated."""

    event_type: ClassVar[str] = "eaip.model_evaluation.evaluation.summary_generated"

    summary_id: str
    evaluation_count: int


class ModelProfileUpdated(DomainEvent):
    """Emitted when a model performance profile is updated."""

    event_type: ClassVar[str] = "eaip.model_evaluation.profile.updated"

    model_id: str
    evaluation_count: int = 0
    benchmark_count: int = 0


class EvaluationDatasetPrepared(DomainEvent):
    """Emitted when an evaluation dataset is prepared."""

    event_type: ClassVar[str] = "eaip.model_evaluation.dataset.prepared"

    dataset_id: str
    name: str
    record_count: int = 0


class EvaluationConfigUpdated(DomainEvent):
    """Emitted when an evaluation configuration is updated."""

    event_type: ClassVar[str] = "eaip.model_evaluation.config.updated"

    config_id: str
    model_id: str


__all__ = [
    "BenchmarkComparisonComputed",
    "BenchmarkCompleted",
    "BenchmarkCreated",
    "BenchmarkFailed",
    "BenchmarkStarted",
    "EvaluationCancelled",
    "EvaluationCompleted",
    "EvaluationConfigUpdated",
    "EvaluationCreated",
    "EvaluationDatasetPrepared",
    "EvaluationFailed",
    "EvaluationStarted",
    "EvaluationSummaryGenerated",
    "MetricRecorded",
    "ModelProfileUpdated",
]
