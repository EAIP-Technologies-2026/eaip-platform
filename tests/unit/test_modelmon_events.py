"""Tests for modelmon domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.modelmon.events import DriftDetected, ModelMetricsRecorded, MonitorAlert


class TestModelMetricsRecorded:
    def test_event_type(self) -> None:
        event = ModelMetricsRecorded(model_id="m1", version="1.0", accuracy=0.95, drift_score=0.02)
        assert event.event_type == "eaip.modelmon.metrics.recorded"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = ModelMetricsRecorded(model_id="m1", version="1.0", accuracy=0.95, drift_score=0.02)
        assert event.model_id == "m1"
        assert event.version == "1.0"
        assert event.accuracy == 0.95
        assert event.drift_score == 0.02

    def test_default_drift_score(self) -> None:
        event = ModelMetricsRecorded(model_id="m1", version="1.0", accuracy=0.95)
        assert event.drift_score == 0.0


class TestDriftDetected:
    def test_event_type(self) -> None:
        event = DriftDetected(
            model_id="m1", version="1.0", drift_type="model", drift_score=0.25, threshold=0.1
        )
        assert event.event_type == "eaip.modelmon.drift.detected"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = DriftDetected(
            model_id="m1", version="1.0", drift_type="data", drift_score=0.3, threshold=0.1
        )
        assert event.model_id == "m1"
        assert event.version == "1.0"
        assert event.drift_type == "data"
        assert event.drift_score == 0.3
        assert event.threshold == 0.1


class TestMonitorAlert:
    def test_event_type(self) -> None:
        event = MonitorAlert(
            model_id="m1",
            version="1.0",
            alert_type="degradation",
            message="Accuracy dropped",
            details={},
        )
        assert event.event_type == "eaip.modelmon.alert"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = MonitorAlert(
            model_id="m1",
            version="1.0",
            alert_type="degradation",
            message="Accuracy dropped from 0.95 to 0.85",
            details={"baseline": 0.95, "current": 0.85},
        )
        assert event.model_id == "m1"
        assert event.alert_type == "degradation"
        assert event.details["baseline"] == 0.95


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(ModelMetricsRecorded, DomainEvent)
        assert issubclass(DriftDetected, DomainEvent)
        assert issubclass(MonitorAlert, DomainEvent)
