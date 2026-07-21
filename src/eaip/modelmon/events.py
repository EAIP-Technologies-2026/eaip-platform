"""Domain events for model monitoring."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class ModelMetricsRecorded(DomainEvent):
    """Emitted when performance metrics are recorded for a model."""

    event_type: ClassVar[str] = "eaip.modelmon.metrics.recorded"

    model_id: str
    version: str
    accuracy: float
    drift_score: float = 0.0


class DriftDetected(DomainEvent):
    """Emitted when drift is detected for a model."""

    event_type: ClassVar[str] = "eaip.modelmon.drift.detected"

    model_id: str
    version: str
    drift_type: str
    drift_score: float
    threshold: float


class MonitorAlert(DomainEvent):
    """Emitted when a monitoring alert is triggered."""

    event_type: ClassVar[str] = "eaip.modelmon.alert"

    model_id: str
    version: str
    alert_type: str
    message: str
    details: dict[str, Any]


__all__ = [
    "DriftDetected",
    "ModelMetricsRecorded",
    "MonitorAlert",
]
