"""Tests for capacity domain events."""

from __future__ import annotations

from eaip.capacity.events import CapacityReportGenerated, MetricRecorded, ThresholdBreached
from eaip.events.event import DomainEvent


class TestMetricRecorded:
    def test_event_type(self) -> None:
        event = MetricRecorded(metric_id="m1", resource_id="res1", metric_name="cpu", value=75.0)
        assert event.event_type == "eaip.capacity.metric.recorded"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = MetricRecorded(metric_id="m1", resource_id="res1", metric_name="cpu", value=75.0)
        assert event.metric_id == "m1"
        assert event.resource_id == "res1"
        assert event.metric_name == "cpu"
        assert event.value == 75.0


class TestCapacityReportGenerated:
    def test_event_type(self) -> None:
        event = CapacityReportGenerated(
            report_id="rpt1",
            resource_id="res1",
            current_usage=75.0,
            predicted_usage=82.5,
            recommended_capacity=90.0,
        )
        assert event.event_type == "eaip.capacity.report.generated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = CapacityReportGenerated(
            report_id="rpt1",
            resource_id="res1",
            current_usage=75.0,
            predicted_usage=82.5,
            recommended_capacity=90.0,
        )
        assert event.report_id == "rpt1"
        assert event.current_usage == 75.0
        assert event.predicted_usage == 82.5
        assert event.recommended_capacity == 90.0


class TestThresholdBreached:
    def test_event_type(self) -> None:
        event = ThresholdBreached(
            resource_id="res1",
            metric_name="cpu",
            current_value=95.0,
            threshold=90.0,
            threshold_type="critical",
        )
        assert event.event_type == "eaip.capacity.threshold.breached"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = ThresholdBreached(
            resource_id="res1",
            metric_name="cpu",
            current_value=95.0,
            threshold=90.0,
            threshold_type="critical",
        )
        assert event.resource_id == "res1"
        assert event.current_value == 95.0
        assert event.threshold_type == "critical"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(MetricRecorded, DomainEvent)
        assert issubclass(CapacityReportGenerated, DomainEvent)
        assert issubclass(ThresholdBreached, DomainEvent)
