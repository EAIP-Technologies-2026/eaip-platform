"""Tests for analytics domain events."""

from __future__ import annotations

import pytest

from eaip.analytics.events import (
    AnomalyDetected,
    DashboardCreated,
    DashboardUpdated,
    KpiEvaluated,
    MetricRecorded,
    ReportGenerated,
    TrendComputed,
)
from eaip.events.event import DomainEvent


class TestMetricRecorded:
    def test_defaults(self) -> None:
        e = MetricRecorded()
        assert e.event_type == "eaip.analytics.metric.recorded"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = MetricRecorded(metric_id="m1", value=42.0, tags={"env": "test"}, source="test")
        assert e.metric_id == "m1"
        assert e.value == 42.0
        assert e.tags == {"env": "test"}
        assert e.source == "test"

    def test_frozen(self) -> None:
        e = MetricRecorded(metric_id="m1")
        with pytest.raises((ValueError, TypeError)):
            e.metric_id = "m2"  # type: ignore[misc]


class TestReportGenerated:
    def test_defaults(self) -> None:
        e = ReportGenerated()
        assert e.event_type == "eaip.analytics.report.generated"
        assert e.metric_ids == ()

    def test_with_values(self) -> None:
        e = ReportGenerated(report_id="r1", name="Test Report", metric_ids=("m1", "m2"))
        assert e.report_id == "r1"
        assert e.metric_ids == ("m1", "m2")


class TestKpiEvaluated:
    def test_defaults(self) -> None:
        e = KpiEvaluated()
        assert e.event_type == "eaip.analytics.kpi.evaluated"
        assert e.status == ""

    def test_with_values(self) -> None:
        e = KpiEvaluated(
            kpi_id="k1", current_value=85.0, target_value=100.0, status="met", progress=0.85
        )
        assert e.kpi_id == "k1"
        assert e.status == "met"
        assert e.progress == 0.85


class TestAnomalyDetected:
    def test_defaults(self) -> None:
        e = AnomalyDetected()
        assert e.event_type == "eaip.analytics.anomaly.detected"
        assert e.severity == ""

    def test_with_values(self) -> None:
        e = AnomalyDetected(
            metric_id="m1", value=100.0, expected_value=50.0, deviation=50.0, severity="high"
        )
        assert e.metric_id == "m1"
        assert e.severity == "high"
        assert e.deviation == 50.0


class TestDashboardCreated:
    def test_defaults(self) -> None:
        e = DashboardCreated()
        assert e.event_type == "eaip.analytics.dashboard.created"
        assert e.widget_count == 0

    def test_with_values(self) -> None:
        e = DashboardCreated(dashboard_id="d1", name="Main", widget_count=5)
        assert e.dashboard_id == "d1"
        assert e.widget_count == 5


class TestDashboardUpdated:
    def test_defaults(self) -> None:
        e = DashboardUpdated()
        assert e.event_type == "eaip.analytics.dashboard.updated"
        assert e.changes == {}

    def test_with_values(self) -> None:
        e = DashboardUpdated(dashboard_id="d1", changes={"name": "New"}, previous_version=1)
        assert e.changes == {"name": "New"}
        assert e.previous_version == 1


class TestTrendComputed:
    def test_defaults(self) -> None:
        e = TrendComputed()
        assert e.event_type == "eaip.analytics.trend.computed"
        assert e.direction == ""

    def test_with_values(self) -> None:
        e = TrendComputed(
            metric_id="m1", direction="up", change_percent=15.5, confidence=0.85, anomaly_count=2
        )
        assert e.direction == "up"
        assert e.change_percent == 15.5
        assert e.anomaly_count == 2


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [
            MetricRecorded,
            ReportGenerated,
            KpiEvaluated,
            AnomalyDetected,
            DashboardCreated,
            DashboardUpdated,
            TrendComputed,
        ]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
