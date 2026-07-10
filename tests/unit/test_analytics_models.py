"""Tests for analytics models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from eaip.analytics.models import (
    AggregationType,
    AnalyticsConfig,
    AnalyticsReport,
    DashboardDefinition,
    DashboardWidget,
    MetricDefinition,
    MetricPoint,
    MetricType,
    TimeSeriesPoint,
    TimeSeriesResult,
    TrendAnalysis,
    TrendDirection,
    WidgetType,
)


class TestMetricType:
    def test_values(self) -> None:
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"
        assert MetricType.TIMER == "timer"

    def test_valid_members(self) -> None:
        assert len(MetricType) == 4


class TestAggregationType:
    def test_values(self) -> None:
        assert AggregationType.SUM == "sum"
        assert AggregationType.AVG == "avg"
        assert AggregationType.MIN == "min"
        assert AggregationType.MAX == "max"
        assert AggregationType.COUNT == "count"
        assert AggregationType.LATEST == "latest"
        assert AggregationType.P50 == "p50"
        assert AggregationType.P95 == "p95"
        assert AggregationType.P99 == "p99"

    def test_valid_members(self) -> None:
        assert len(AggregationType) == 9


class TestTrendDirection:
    def test_values(self) -> None:
        assert TrendDirection.UP == "up"
        assert TrendDirection.DOWN == "down"
        assert TrendDirection.STABLE == "stable"
        assert TrendDirection.VOLATILE == "volatile"


class TestWidgetType:
    def test_values(self) -> None:
        assert WidgetType.TIMESERIES == "timeseries"
        assert WidgetType.COUNTER == "counter"
        assert WidgetType.GAUGE == "gauge"
        assert WidgetType.HEATMAP == "heatmap"
        assert WidgetType.TABLE == "table"


class TestMetricDefinition:
    def test_defaults(self) -> None:
        m = MetricDefinition(id="m1", name="Test Metric")
        assert m.id == "m1"
        assert m.name == "Test Metric"
        assert m.description == ""
        assert m.type is MetricType.COUNTER
        assert m.unit == ""
        assert m.aggregation is AggregationType.SUM
        assert m.tags == ()
        assert m.metadata == {}
        assert m.enabled is True

    def test_custom(self) -> None:
        m = MetricDefinition(
            id="m2",
            name="CPU Usage",
            description="CPU utilization percentage",
            type=MetricType.GAUGE,
            unit="%",
            aggregation=AggregationType.AVG,
            tags=("system", "cpu"),
            metadata={"source": "os"},
            enabled=False,
        )
        assert m.type is MetricType.GAUGE
        assert m.unit == "%"
        assert m.aggregation is AggregationType.AVG
        assert m.tags == ("system", "cpu")
        assert m.metadata == {"source": "os"}
        assert m.enabled is False

    def test_frozen(self) -> None:
        m = MetricDefinition(id="m1", name="Test")
        with pytest.raises(ValueError):
            m.name = "Changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            MetricDefinition(id="m1", name="Test", extra_field="x")  # type: ignore[call-arg]


class TestMetricPoint:
    def test_defaults(self) -> None:
        now = datetime.now(timezone.utc)
        p = MetricPoint(metric_id="m1", timestamp=now, value=42.0)
        assert p.metric_id == "m1"
        assert p.timestamp == now
        assert p.value == 42.0
        assert p.tags == {}
        assert p.source == ""
        assert p.labels == {}

    def test_with_all_fields(self) -> None:
        now = datetime.now(timezone.utc)
        p = MetricPoint(
            metric_id="m1", timestamp=now, value=99.5,
            tags={"env": "prod"}, source="test", labels={"host": "h1"},
        )
        assert p.tags == {"env": "prod"}
        assert p.source == "test"
        assert p.labels == {"host": "h1"}

    def test_frozen(self) -> None:
        now = datetime.now(timezone.utc)
        p = MetricPoint(metric_id="m1", timestamp=now, value=1.0)
        with pytest.raises(ValueError):
            p.value = 2.0  # type: ignore[misc]


class TestTimeSeriesPoint:
    def test_defaults(self) -> None:
        now = datetime.now(timezone.utc)
        p = TimeSeriesPoint(timestamp=now, value=10.0)
        assert p.timestamp == now
        assert p.value == 10.0
        assert p.label == ""

    def test_with_label(self) -> None:
        now = datetime.now(timezone.utc)
        p = TimeSeriesPoint(timestamp=now, value=10.0, label="avg")
        assert p.label == "avg"


class TestTimeSeriesResult:
    def test_defaults(self) -> None:
        now = datetime.now(timezone.utc)
        r = TimeSeriesResult(metric_id="m1", start_time=now, end_time=now)
        assert r.metric_id == "m1"
        assert r.points == ()
        assert r.aggregation is AggregationType.SUM
        assert r.interval_seconds == 60.0

    def test_with_points(self) -> None:
        now = datetime.now(timezone.utc)
        points = (TimeSeriesPoint(timestamp=now, value=1.0), TimeSeriesPoint(timestamp=now, value=2.0))
        r = TimeSeriesResult(
            metric_id="m1", points=points, aggregation=AggregationType.AVG,
            start_time=now, end_time=now, interval_seconds=30.0,
        )
        assert len(r.points) == 2
        assert r.aggregation is AggregationType.AVG
        assert r.interval_seconds == 30.0


class TestAnalyticsReport:
    def test_defaults(self) -> None:
        now = datetime.now(timezone.utc)
        r = AnalyticsReport(id="r1", name="Report1", time_range=(now, now))
        assert r.id == "r1"
        assert r.description == ""
        assert r.metric_ids == ()
        assert r.interval == 60.0
        assert r.results == {}

    def test_with_results(self) -> None:
        now = datetime.now(timezone.utc)
        tr = TimeSeriesResult(metric_id="m1", start_time=now, end_time=now)
        r = AnalyticsReport(
            id="r2", name="Full Report", metric_ids=("m1",),
            time_range=(now, now), results={"m1": tr},
            metadata={"author": "test"},
        )
        assert len(r.metric_ids) == 1
        assert "m1" in r.results
        assert r.metadata == {"author": "test"}

    def test_frozen(self) -> None:
        now = datetime.now(timezone.utc)
        r = AnalyticsReport(id="r1", name="R", time_range=(now, now))
        with pytest.raises(ValueError):
            r.name = "Changed"  # type: ignore[misc]


class TestTrendAnalysis:
    def test_defaults(self) -> None:
        t = TrendAnalysis(metric_id="m1")
        assert t.metric_id == "m1"
        assert t.direction is TrendDirection.STABLE
        assert t.change_percent == 0.0
        assert t.confidence == 0.0
        assert t.period_comparison == {}
        assert t.forecast_values == ()
        assert t.seasonality_detected is False
        assert t.anomaly_count == 0

    def test_custom(self) -> None:
        t = TrendAnalysis(
            metric_id="m1", direction=TrendDirection.UP,
            change_percent=15.5, confidence=0.85,
            period_comparison={"prev": 100.0, "current": 115.5},
            forecast_values=(120.0, 130.0),
            seasonality_detected=True, anomaly_count=2,
        )
        assert t.direction is TrendDirection.UP
        assert t.change_percent == 15.5
        assert t.anomaly_count == 2
        assert t.seasonality_detected is True


class TestDashboardWidget:
    def test_defaults(self) -> None:
        w = DashboardWidget(id="w1")
        assert w.id == "w1"
        assert w.type is WidgetType.TIMESERIES
        assert w.metric_ids == ()
        assert w.title == ""
        assert w.width == 1
        assert w.height == 1
        assert w.config == {}

    def test_custom(self) -> None:
        w = DashboardWidget(
            id="w2", type=WidgetType.GAUGE, metric_ids=("m1",),
            title="CPU", width=2, height=2, config={"min": 0, "max": 100},
        )
        assert w.type is WidgetType.GAUGE
        assert w.metric_ids == ("m1",)
        assert w.width == 2

    def test_frozen(self) -> None:
        w = DashboardWidget(id="w1")
        with pytest.raises(ValueError):
            w.title = "Changed"  # type: ignore[misc]


class TestDashboardDefinition:
    def test_defaults(self) -> None:
        d = DashboardDefinition(id="d1", name="Main")
        assert d.id == "d1"
        assert d.description == ""
        assert d.widgets == ()
        assert d.refresh_interval_seconds == 60.0

    def test_with_widgets(self) -> None:
        w = DashboardWidget(id="w1", type=WidgetType.TIMESERIES, metric_ids=("m1",))
        d = DashboardDefinition(id="d1", name="Main", widgets=(w,), refresh_interval_seconds=30.0)
        assert len(d.widgets) == 1
        assert d.widgets[0].id == "w1"

    def test_frozen(self) -> None:
        d = DashboardDefinition(id="d1", name="Main")
        with pytest.raises(ValueError):
            d.name = "Changed"  # type: ignore[misc]


class TestAnalyticsConfig:
    def test_defaults(self) -> None:
        c = AnalyticsConfig()
        assert c.retention_days == 90
        assert c.aggregation_interval_seconds == 60.0
        assert c.max_data_points == 10000
        assert c.enable_trend_detection is True
        assert c.enable_anomaly_detection is True

    def test_custom(self) -> None:
        c = AnalyticsConfig(
            retention_days=30, aggregation_interval_seconds=300.0,
            max_data_points=5000, enable_trend_detection=False,
        )
        assert c.retention_days == 30
        assert c.aggregation_interval_seconds == 300.0
        assert c.enable_trend_detection is False

    def test_frozen(self) -> None:
        c = AnalyticsConfig()
        with pytest.raises(ValueError):
            c.retention_days = 60  # type: ignore[misc]
