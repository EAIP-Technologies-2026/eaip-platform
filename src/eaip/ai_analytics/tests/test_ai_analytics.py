"""Tests for the AI Analytics package."""

from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.ai_analytics.events import (
    AiAnalyticsConfigUpdated,
    AiAnalyticsDashboardCreated,
    AiAnalyticsDashboardUpdated,
    AiAnalyticsExportCompleted,
    AiAnalyticsForecastGenerated,
    AiAnalyticsInsightGenerated,
    AiAnalyticsMetricRecorded,
    AiAnalyticsReportGenerated,
    AiAnalyticsTrendComputed,
    AiAnomalyDetected,
    AiCostReported,
    AiErrorRateReported,
    AiLatencyReported,
    AiModelUsageReported,
    AiTokenUsageReported,
)
from eaip.ai_analytics.exceptions import (
    AiAnalyticsConfigError,
    AiAnalyticsDashboardError,
    AiAnalyticsError,
    AiAnalyticsExportError,
    AiAnalyticsMetricError,
    AiAnalyticsQueryError,
    AiAnalyticsReportError,
    AiAnomalyDetectionError,
)
from eaip.ai_analytics.models import (
    AiAnalyticsConfig,
    AiAnalyticsDashboard,
    AiAnalyticsDashboardWidget,
    AiAnalyticsExport,
    AiAnalyticsForecast,
    AiAnalyticsInsight,
    AiAnalyticsInsightSeverity,
    AiAnalyticsMetric,
    AiAnalyticsMetricType,
    AiAnalyticsReport,
    AiAnalyticsReportPeriod,
    AiAnalyticsTrend,
    AiAnomalyDetectionResult,
    AiCostMetrics,
    AiErrorMetrics,
    AiLatencyMetrics,
    AiModelUsageMetrics,
    AiTokenUsageMetrics,
)
from eaip.ai_analytics.service import AiAnalyticsService
from eaip.shared.time import utc_now

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestAiAnalyticsConfig:
    def test_defaults(self) -> None:
        c = AiAnalyticsConfig()
        assert c.enabled is True
        assert c.retention_days == 90

    def test_frozen(self) -> None:
        c = AiAnalyticsConfig()
        with pytest.raises(ValueError):  # frozen
            c.enabled = False


class TestAiAnalyticsMetric:
    def test_defaults(self) -> None:
        m = AiAnalyticsMetric(id="m1", name="test")
        assert m.type == AiAnalyticsMetricType.CUSTOM
        assert m.value == 0.0

    def test_frozen(self) -> None:
        m = AiAnalyticsMetric(id="m1", name="test")
        with pytest.raises(ValueError):
            m.value = 42.0


class TestAiModelUsageMetrics:
    def test_defaults(self) -> None:
        u = AiModelUsageMetrics()
        assert u.total_requests == 0
        assert u.successful_requests == 0


class TestAiTokenUsageMetrics:
    def test_defaults(self) -> None:
        t = AiTokenUsageMetrics()
        assert t.total_tokens == 0
        assert t.prompt_tokens == 0


class TestAiLatencyMetrics:
    def test_defaults(self) -> None:
        lat = AiLatencyMetrics()
        assert lat.avg_latency_ms == 0.0
        assert lat.p95_latency_ms == 0.0


class TestAiErrorMetrics:
    def test_defaults(self) -> None:
        e = AiErrorMetrics()
        assert e.total_errors == 0
        assert e.error_rate == 0.0


class TestAiCostMetrics:
    def test_defaults(self) -> None:
        c = AiCostMetrics()
        assert c.total_cost == 0.0
        assert c.currency == "USD"


class TestAiAnalyticsReport:
    def test_create(self) -> None:
        now = utc_now()
        r = AiAnalyticsReport(
            id="r1",
            name="Test Report",
            time_range=(now, now + timedelta(hours=1)),
        )
        assert r.period == AiAnalyticsReportPeriod.DAILY
        assert r.model_ids == ()


class TestAiAnalyticsDashboard:
    def test_create_with_widgets(self) -> None:
        w = AiAnalyticsDashboardWidget(id="w1", title="Widget")
        d = AiAnalyticsDashboard(id="d1", name="Dashboard", widgets=(w,))
        assert len(d.widgets) == 1
        assert d.widgets[0].title == "Widget"


class TestAiAnomalyDetectionResult:
    def test_create(self) -> None:
        a = AiAnomalyDetectionResult(
            id="a1",
            metric_id="m1",
            value=42.0,
            expected_value=10.0,
            deviation=3.2,
        )
        assert a.severity == AiAnalyticsInsightSeverity.WARNING


class TestAiAnalyticsTrend:
    def test_defaults(self) -> None:
        t = AiAnalyticsTrend(metric_id="m1")
        assert t.direction == "stable"
        assert t.change_percent == 0.0


class TestAiAnalyticsForecast:
    def test_create(self) -> None:
        f = AiAnalyticsForecast(id="f1", metric_id="m1")
        assert f.horizon_hours == 24.0


class TestAiAnalyticsInsight:
    def test_create(self) -> None:
        i = AiAnalyticsInsight(id="i1", title="Insight")
        assert i.severity == AiAnalyticsInsightSeverity.INFO


class TestAiAnalyticsExport:
    def test_create(self) -> None:
        e = AiAnalyticsExport(id="e1", report_id="r1")
        assert e.format == "json"
        assert e.success is True


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestAiAnalyticsEvents:
    def test_config_updated(self) -> None:
        e = AiAnalyticsConfigUpdated()
        assert e.event_type == "eaip.ai_analytics.config.updated"

    def test_metric_recorded(self) -> None:
        e = AiAnalyticsMetricRecorded(metric_id="m1", value=42.0)
        assert e.event_type == "eaip.ai_analytics.metric.recorded"

    def test_report_generated(self) -> None:
        e = AiAnalyticsReportGenerated(report_id="r1")
        assert e.event_type == "eaip.ai_analytics.report.generated"

    def test_dashboard_created(self) -> None:
        e = AiAnalyticsDashboardCreated(dashboard_id="d1")
        assert e.event_type == "eaip.ai_analytics.dashboard.created"

    def test_dashboard_updated(self) -> None:
        e = AiAnalyticsDashboardUpdated(dashboard_id="d1")
        assert e.event_type == "eaip.ai_analytics.dashboard.updated"

    def test_anomaly_detected(self) -> None:
        e = AiAnomalyDetected(metric_id="m1", value=42.0)
        assert e.event_type == "eaip.ai_analytics.anomaly.detected"

    def test_trend_computed(self) -> None:
        e = AiAnalyticsTrendComputed(metric_id="m1")
        assert e.event_type == "eaip.ai_analytics.trend.computed"

    def test_forecast_generated(self) -> None:
        e = AiAnalyticsForecastGenerated(forecast_id="f1", metric_id="m1")
        assert e.event_type == "eaip.ai_analytics.forecast.generated"

    def test_insight_generated(self) -> None:
        e = AiAnalyticsInsightGenerated(insight_id="i1")
        assert e.event_type == "eaip.ai_analytics.insight.generated"

    def test_export_completed(self) -> None:
        e = AiAnalyticsExportCompleted(export_id="e1")
        assert e.event_type == "eaip.ai_analytics.export.completed"

    def test_model_usage_reported(self) -> None:
        e = AiModelUsageReported(model_id="gpt-4")
        assert e.event_type == "eaip.ai_analytics.model_usage.reported"

    def test_token_usage_reported(self) -> None:
        e = AiTokenUsageReported(model_id="gpt-4")
        assert e.event_type == "eaip.ai_analytics.token_usage.reported"

    def test_latency_reported(self) -> None:
        e = AiLatencyReported(model_id="gpt-4")
        assert e.event_type == "eaip.ai_analytics.latency.reported"

    def test_error_rate_reported(self) -> None:
        e = AiErrorRateReported(model_id="gpt-4")
        assert e.event_type == "eaip.ai_analytics.error_rate.reported"

    def test_cost_reported(self) -> None:
        e = AiCostReported(model_id="gpt-4")
        assert e.event_type == "eaip.ai_analytics.cost.reported"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestAiAnalyticsExceptions:
    def test_base_error(self) -> None:
        e = AiAnalyticsError("test")
        assert "test" in str(e)

    def test_config_error(self) -> None:
        e = AiAnalyticsConfigError("invalid config")
        assert isinstance(e, AiAnalyticsError)

    def test_metric_error(self) -> None:
        e = AiAnalyticsMetricError("metric error")
        assert isinstance(e, AiAnalyticsError)

    def test_report_error(self) -> None:
        e = AiAnalyticsReportError("report error")
        assert isinstance(e, AiAnalyticsError)

    def test_dashboard_error(self) -> None:
        e = AiAnalyticsDashboardError("dashboard error")
        assert isinstance(e, AiAnalyticsError)

    def test_export_error(self) -> None:
        e = AiAnalyticsExportError("export error")
        assert isinstance(e, AiAnalyticsError)

    def test_query_error(self) -> None:
        e = AiAnalyticsQueryError("query error")
        assert isinstance(e, AiAnalyticsError)

    def test_anomaly_detection_error(self) -> None:
        e = AiAnomalyDetectionError("anomaly error")
        assert isinstance(e, AiAnalyticsError)


# ---------------------------------------------------------------------------
# Service — Metrics
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceMetrics:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_record_metric(self, service: AiAnalyticsService) -> None:
        m = await service.record_metric("m1", 42.0, name="test-metric")
        assert m.id == "m1"
        assert m.value == 42.0

    async def test_get_metric(self, service: AiAnalyticsService) -> None:
        await service.record_metric("m1", 42.0)
        m = await service.get_metric("m1")
        assert m.id == "m1"

    async def test_get_metric_not_found(self, service: AiAnalyticsService) -> None:
        with pytest.raises(AiAnalyticsMetricError):
            await service.get_metric("nonexistent")

    async def test_list_metrics(self, service: AiAnalyticsService) -> None:
        await service.record_metric("m1", 1.0, metric_type=AiAnalyticsMetricType.TOKENS)
        await service.record_metric("m2", 2.0, metric_type=AiAnalyticsMetricType.LATENCY)
        all_m = await service.list_metrics()
        assert len(all_m) == 2
        tokens = await service.list_metrics(metric_type=AiAnalyticsMetricType.TOKENS)
        assert len(tokens) == 1

    async def test_record_metric_disabled(self, service: AiAnalyticsService) -> None:
        await service.update_config(enabled=False)
        with pytest.raises(AiAnalyticsConfigError):
            await service.record_metric("m1", 42.0)


# ---------------------------------------------------------------------------
# Service — Usage
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceUsage:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_report_model_usage(self, service: AiAnalyticsService) -> None:
        u = AiModelUsageMetrics(model_id="gpt-4", total_requests=100)
        result = await service.report_model_usage(u)
        assert result.total_requests == 100

    async def test_report_token_usage(self, service: AiAnalyticsService) -> None:
        t = AiTokenUsageMetrics(model_id="gpt-4", total_tokens=500)
        result = await service.report_token_usage(t)
        assert result.total_tokens == 500

    async def test_report_latency(self, service: AiAnalyticsService) -> None:
        lat = AiLatencyMetrics(model_id="gpt-4", avg_latency_ms=150.0)
        result = await service.report_latency(lat)
        assert result.avg_latency_ms == 150.0

    async def test_report_errors(self, service: AiAnalyticsService) -> None:
        e = AiErrorMetrics(model_id="gpt-4", total_errors=5)
        result = await service.report_errors(e)
        assert result.total_errors == 5

    async def test_report_cost(self, service: AiAnalyticsService) -> None:
        c = AiCostMetrics(model_id="gpt-4", total_cost=12.50)
        result = await service.report_cost(c)
        assert result.total_cost == 12.50


# ---------------------------------------------------------------------------
# Service — Reports
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceReports:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_generate_report(self, service: AiAnalyticsService) -> None:
        now = utc_now()
        u = AiModelUsageMetrics(model_id="gpt-4", total_requests=100)
        await service.report_model_usage(u)
        report = await service.generate_report(
            model_ids=["gpt-4"],
            time_range=(now - timedelta(days=1), now),
        )
        assert report.id.startswith("ai_report_")
        assert "gpt-4" in report.model_ids

    async def test_generate_report_no_models(self, service: AiAnalyticsService) -> None:
        with pytest.raises(AiAnalyticsReportError):
            await service.generate_report(model_ids=[])


# ---------------------------------------------------------------------------
# Service — Dashboards
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceDashboards:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_create_dashboard(self, service: AiAnalyticsService) -> None:
        d = await service.create_dashboard("My Dashboard")
        assert d.name == "My Dashboard"
        assert d.id.startswith("ai_dash_")

    async def test_get_dashboard(self, service: AiAnalyticsService) -> None:
        d = await service.create_dashboard("Test")
        result = await service.get_dashboard(d.id)
        assert result.id == d.id

    async def test_get_dashboard_not_found(self, service: AiAnalyticsService) -> None:
        with pytest.raises(AiAnalyticsDashboardError):
            await service.get_dashboard("nonexistent")

    async def test_list_dashboards(self, service: AiAnalyticsService) -> None:
        await service.create_dashboard("D1")
        await service.create_dashboard("D2")
        all_d = await service.list_dashboards()
        assert len(all_d) == 2

    async def test_delete_dashboard(self, service: AiAnalyticsService) -> None:
        d = await service.create_dashboard("To Delete")
        await service.delete_dashboard(d.id)
        assert len(await service.list_dashboards()) == 0

    async def test_delete_dashboard_not_found(self, service: AiAnalyticsService) -> None:
        with pytest.raises(AiAnalyticsDashboardError):
            await service.delete_dashboard("nonexistent")


# ---------------------------------------------------------------------------
# Service — Anomaly Detection
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceAnomaly:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_detect_anomalies(self, service: AiAnalyticsService) -> None:
        values: list[float] = [10, 12, 11, 13, 10, 100, 11, 12]
        results = await service.detect_anomalies("m1", values)
        assert len(results) >= 1

    async def test_detect_anomalies_empty(self, service: AiAnalyticsService) -> None:
        results = await service.detect_anomalies("m1", [])
        assert results == []

    async def test_detect_anomalies_disabled(self, service: AiAnalyticsService) -> None:
        await service.update_config(anomaly_detection_enabled=False)
        with pytest.raises(AiAnomalyDetectionError):
            await service.detect_anomalies("m1", [1, 2, 3])

    async def test_list_anomalies(self, service: AiAnalyticsService) -> None:
        await service.detect_anomalies("m1", [10, 10, 100, 10])
        anomalies = await service.list_anomalies(metric_id="m1")
        assert len(anomalies) >= 1


# ---------------------------------------------------------------------------
# Service — Trends
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceTrends:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_compute_trend_up(self, service: AiAnalyticsService) -> None:
        values: list[float] = [10, 20, 30, 40, 50]
        trend = await service.compute_trend("m1", values)
        assert trend.direction == "up"
        assert trend.change_percent > 0

    async def test_compute_trend_down(self, service: AiAnalyticsService) -> None:
        values: list[float] = [50, 40, 30, 20, 10]
        trend = await service.compute_trend("m1", values)
        assert trend.direction == "down"

    async def test_compute_trend_stable(self, service: AiAnalyticsService) -> None:
        values: list[float] = [10, 11, 10, 11, 10]
        trend = await service.compute_trend("m1", values)
        assert trend.direction == "stable"

    async def test_compute_trend_single(self, service: AiAnalyticsService) -> None:
        trend = await service.compute_trend("m1", [42])
        assert trend.direction == "stable"

    async def test_list_trends(self, service: AiAnalyticsService) -> None:
        await service.compute_trend("m1", [1, 2, 3])
        trends = await service.list_trends(metric_id="m1")
        assert len(trends) == 1


# ---------------------------------------------------------------------------
# Service — Forecasts
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceForecasts:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_generate_forecast(self, service: AiAnalyticsService) -> None:
        now = utc_now()
        timestamps = [now - timedelta(hours=i) for i in range(10, 0, -1)]
        values = [float(i) for i in range(10, 0, -1)]
        forecast = await service.generate_forecast("m1", values, timestamps)
        assert len(forecast.forecast_points) > 0

    async def test_get_forecast(self, service: AiAnalyticsService) -> None:
        now = utc_now()
        timestamps = [now - timedelta(hours=i) for i in range(5, 0, -1)]
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        f = await service.generate_forecast("m1", values, timestamps)
        result = await service.get_forecast(f.id)
        assert result.id == f.id

    async def test_get_forecast_not_found(self, service: AiAnalyticsService) -> None:
        with pytest.raises(AiAnalyticsQueryError):
            await service.get_forecast("nonexistent")

    async def test_generate_forecast_disabled(self, service: AiAnalyticsService) -> None:
        await service.update_config(forecast_enabled=False)
        with pytest.raises(AiAnalyticsQueryError):
            await service.generate_forecast("m1", [1, 2], [utc_now(), utc_now()])


# ---------------------------------------------------------------------------
# Service — Insights
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceInsights:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_generate_insight(self, service: AiAnalyticsService) -> None:
        insight = await service.generate_insight(
            title="High Latency",
            description="Latency is above threshold",
            severity=AiAnalyticsInsightSeverity.WARNING,
            recommendation="Consider scaling up",
        )
        assert insight.title == "High Latency"
        assert insight.id.startswith("insight_")

    async def test_list_insights(self, service: AiAnalyticsService) -> None:
        await service.generate_insight("I1")
        await service.generate_insight("I2", severity=AiAnalyticsInsightSeverity.CRITICAL)
        all_i = await service.list_insights()
        assert len(all_i) == 2
        crit = await service.list_insights(severity=AiAnalyticsInsightSeverity.CRITICAL)
        assert len(crit) == 1


# ---------------------------------------------------------------------------
# Service — Exports
# ---------------------------------------------------------------------------


class TestAiAnalyticsServiceExports:
    @pytest.fixture
    def service(self) -> AiAnalyticsService:
        return AiAnalyticsService()

    async def test_export_report(self, service: AiAnalyticsService) -> None:
        export = await service.export_report("r1", format="csv", destination="storage://exports")
        assert export.report_id == "r1"
        assert export.format == "csv"

    async def test_get_export(self, service: AiAnalyticsService) -> None:
        export = await service.export_report("r1")
        result = await service.get_export(export.id)
        assert result.id == export.id

    async def test_get_export_not_found(self, service: AiAnalyticsService) -> None:
        with pytest.raises(AiAnalyticsExportError):
            await service.get_export("nonexistent")

    async def test_list_exports(self, service: AiAnalyticsService) -> None:
        await service.export_report("r1")
        await service.export_report("r2")
        exports = await service.list_exports()
        assert len(exports) == 2

    async def test_export_disabled(self, service: AiAnalyticsService) -> None:
        await service.update_config(export_enabled=False)
        with pytest.raises(AiAnalyticsExportError):
            await service.export_report("r1")
