"""ModelMonitor — tracks model versions, detects drift, and records performance metrics."""

from __future__ import annotations

from collections import defaultdict

from eaip.logging.context import get_logger
from eaip.modelmon.events import DriftDetected, ModelMetricsRecorded, MonitorAlert
from eaip.modelmon.exceptions import ModelNotFoundError
from eaip.modelmon.models import (
    DriftMetric,
    DriftReport,
    ModelMetrics,
    MonitorConfig,
)


class ModelMonitor:
    """Central service for monitoring models, detecting drift, and recording metrics."""

    def __init__(self, config: MonitorConfig | None = None) -> None:
        self._config = config or MonitorConfig()
        self._metrics: dict[str, list[ModelMetrics]] = defaultdict(list)
        self._versions: dict[str, list[str]] = defaultdict(list)
        self._log = get_logger("eaip.modelmon.monitor")

    @property
    def config(self) -> MonitorConfig:
        return self._config

    async def track_version(self, model_id: str, version: str) -> None:
        """Register a model version for monitoring."""
        versions = self._versions[model_id]
        if version not in versions:
            versions.append(version)
            self._log.info("modelmon.version.tracked", model_id=model_id, version=version)

    async def record_metrics(
        self, model_id: str, version: str, metrics: ModelMetrics
    ) -> ModelMetrics:
        """Record performance metrics for a model version."""
        stored = ModelMetrics(
            model_id=model_id,
            version=version,
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            f1_score=metrics.f1_score,
            latency_ms=metrics.latency_ms,
            sample_count=metrics.sample_count,
            metadata=metrics.metadata,
        )
        self._metrics[model_id].append(stored)
        self._trim_history(model_id)

        drift_score = await self._compute_drift(model_id, version)
        event = ModelMetricsRecorded(
            model_id=model_id, version=version, accuracy=stored.accuracy, drift_score=drift_score
        )
        self._log.info("modelmon.metrics.recorded", model_id=model_id, version=version)
        return stored

    async def detect_drift(self, model_id: str, version: str) -> DriftReport:
        """Detect drift for a model version based on recent metrics."""
        if model_id not in self._metrics:
            raise ModelNotFoundError(f"Model '{model_id}' not found")

        recent = self._metrics[model_id]
        if not recent:
            raise ModelNotFoundError(f"No metrics recorded for model '{model_id}'")

        baseline = recent[0]
        latest = recent[-1]

        drift_score = abs(baseline.accuracy - latest.accuracy)
        is_drifted = drift_score > self._config.drift_threshold

        report = DriftReport(
            model_id=model_id,
            version=version,
            drift_metric=DriftMetric.MODEL,
            drift_score=min(drift_score, 1.0),
            threshold=self._config.drift_threshold,
            is_drifted=is_drifted,
        )

        if is_drifted:
            drift_event = DriftDetected(
                model_id=model_id,
                version=version,
                drift_type=DriftMetric.MODEL.value,
                drift_score=report.drift_score,
                threshold=report.threshold,
            )
            self._log.info("modelmon.drift.detected", model_id=model_id, version=version)

        return report

    async def check_degradation(self, model_id: str, version: str) -> bool:
        """Check if a model has degraded beyond the degradation threshold."""
        if model_id not in self._metrics:
            raise ModelNotFoundError(f"Model '{model_id}' not found")

        recent = self._metrics[model_id]
        if len(recent) < 2:
            return False

        baseline = recent[0]
        latest = recent[-1]
        degradation = baseline.accuracy - latest.accuracy

        if degradation > self._config.degradation_threshold:
            alert = MonitorAlert(
                model_id=model_id,
                version=version,
                alert_type="degradation",
                message=f"Model accuracy degraded by {degradation:.3f}",
                details={
                    "baseline_accuracy": baseline.accuracy,
                    "current_accuracy": latest.accuracy,
                },
            )
            self._log.info("modelmon.degradation.detected", model_id=model_id, version=version)
            return True

        return False

    async def get_metrics(self, model_id: str) -> list[ModelMetrics]:
        """Retrieve all recorded metrics for a model."""
        return list(self._metrics.get(model_id, []))

    async def list_tracked_models(self) -> list[tuple[str, list[str]]]:
        """List all tracked models and their versions."""
        return [(mid, list(vers)) for mid, vers in self._versions.items()]

    def _trim_history(self, model_id: str) -> None:
        """Trim metrics history to the configured maximum."""
        points = self._metrics[model_id]
        if len(points) > self._config.max_metrics_history:
            self._metrics[model_id] = points[-self._config.max_metrics_history :]

    async def _compute_drift(self, model_id: str, _version: str) -> float:
        """Compute a simple drift score from recorded metrics."""
        recent = self._metrics[model_id]
        if len(recent) < 2:
            return 0.0
        baseline = recent[0]
        latest = recent[-1]
        return min(abs(baseline.accuracy - latest.accuracy), 1.0)


__all__ = ["ModelMonitor"]
