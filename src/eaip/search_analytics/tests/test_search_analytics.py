"""Tests for search_analytics — models, events, exceptions, service, health, integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.events.event import DomainEvent
from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.health.checks import HealthStatus
from eaip.search_analytics.events import (
    SearchAbandonmentAnalysisCompleted,
    SearchAnalyticsAlertTriggered,
    SearchAnalyticsConfigUpdated,
    SearchAnalyticsDashboardCreated,
    SearchAnalyticsDashboardUpdated,
    SearchAnalyticsReportGenerated,
    SearchClickThroughLogged,
    SearchFunnelAnalysisCompleted,
    SearchMetricsCollected,
    SearchPerformanceReportGenerated,
    SearchPopularQueryIdentified,
    SearchQueryLogged,
    SearchSessionAbandoned,
    SearchSessionCompleted,
    SearchSessionStarted,
    SearchTrendComputed,
    SearchZeroResultQueryIdentified,
)
from eaip.search_analytics.exceptions import (
    SearchAnalyticsAlertError,
    SearchAnalyticsConfigError,
    SearchAnalyticsDashboardError,
    SearchAnalyticsError,
    SearchAnalyticsQueryError,
    SearchAnalyticsReportError,
    SearchMetricsCollectionError,
)
from eaip.search_analytics.health import SearchAnalyticsHealthCheck
from eaip.search_analytics.integration import SearchAnalyticsRuntimeModule
from eaip.search_analytics.models import (
    SearchAbandonmentAnalysis,
    SearchAnalyticsAlert,
    SearchAnalyticsConfig,
    SearchAnalyticsDashboard,
    SearchAnalyticsReport,
    SearchClickThrough,
    SearchFunnel,
    SearchFunnelAnalysis,
    SearchFunnelStep,
    SearchMetrics,
    SearchMetricsPeriod,
    SearchPerformanceReport,
    SearchPopularQuery,
    SearchQueryLog,
    SearchSession,
    SearchSessionStatus,
    SearchTrend,
    SearchTrendPeriod,
    SearchZeroResultQuery,
)
from eaip.search_analytics.service import SearchAnalyticsService

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestSearchMetricsPeriod:
    def test_values(self) -> None:
        assert SearchMetricsPeriod.LAST_HOUR.value == "last_hour"
        assert SearchMetricsPeriod.LAST_24H.value == "last_24h"
        assert SearchMetricsPeriod.LAST_7D.value == "last_7d"
        assert SearchMetricsPeriod.LAST_30D.value == "last_30d"
        assert SearchMetricsPeriod.CUSTOM.value == "custom"


class TestSearchTrendPeriod:
    def test_values(self) -> None:
        assert SearchTrendPeriod.DAILY.value == "daily"
        assert SearchTrendPeriod.WEEKLY.value == "weekly"
        assert SearchTrendPeriod.MONTHLY.value == "monthly"
        assert SearchTrendPeriod.QUARTERLY.value == "quarterly"
        assert SearchTrendPeriod.YEARLY.value == "yearly"


class TestSearchSessionStatus:
    def test_values(self) -> None:
        assert SearchSessionStatus.ACTIVE.value == "active"
        assert SearchSessionStatus.COMPLETED.value == "completed"
        assert SearchSessionStatus.ABANDONED.value == "abandoned"
        assert SearchSessionStatus.TIMEOUT.value == "timeout"


class TestSearchAnalyticsConfig:
    def test_defaults(self) -> None:
        c = SearchAnalyticsConfig()
        assert c.enabled is True
        assert c.logging_enabled is True
        assert c.retention_days == 90
        assert c.popular_query_threshold == 10

    def test_frozen(self) -> None:
        c = SearchAnalyticsConfig()
        with pytest.raises(ValueError):
            c.enabled = False


class TestSearchQueryLog:
    def test_defaults(self) -> None:
        ql = SearchQueryLog(id="q1", query="test")
        assert ql.id == "q1"
        assert ql.query == "test"
        assert ql.result_count == 0
        assert ql.duration_ms == 0.0


class TestSearchMetrics:
    def test_defaults(self) -> None:
        m = SearchMetrics()
        assert m.total_queries == 0
        assert m.unique_users == 0
        assert m.period == SearchMetricsPeriod.LAST_24H


class TestSearchPerformanceReport:
    def test_defaults(self) -> None:
        r = SearchPerformanceReport(id="p1")
        assert r.id == "p1"
        assert r.period == SearchMetricsPeriod.LAST_24H
        assert r.error_rate == 0.0
        assert r.metrics is None


class TestSearchTrend:
    def test_defaults(self) -> None:
        t = SearchTrend(metric_name="avg_duration_ms")
        assert t.metric_name == "avg_duration_ms"
        assert t.direction == "stable"
        assert t.period == SearchTrendPeriod.DAILY


class TestSearchAnalyticsReport:
    def test_defaults(self) -> None:
        r = SearchAnalyticsReport(id="r1")
        assert r.id == "r1"
        assert r.period == SearchMetricsPeriod.LAST_24H
        assert r.trends == ()


class TestSearchAnalyticsDashboard:
    def test_defaults(self) -> None:
        d = SearchAnalyticsDashboard(id="d1", name="Test Dashboard")
        assert d.id == "d1"
        assert d.name == "Test Dashboard"
        assert d.report_ids == ()


class TestSearchPopularQuery:
    def test_defaults(self) -> None:
        pq = SearchPopularQuery(query="test query")
        assert pq.query == "test query"
        assert pq.count == 0


class TestSearchZeroResultQuery:
    def test_defaults(self) -> None:
        zr = SearchZeroResultQuery(query="no results")
        assert zr.query == "no results"
        assert zr.count == 0


class TestSearchClickThrough:
    def test_defaults(self) -> None:
        ct = SearchClickThrough(query="test", result_id="r1")
        assert ct.query == "test"
        assert ct.result_id == "r1"
        assert ct.result_position == 0


class TestSearchSession:
    def test_defaults(self) -> None:
        s = SearchSession(id="s1")
        assert s.id == "s1"
        assert s.status == SearchSessionStatus.ACTIVE
        assert s.query_count == 0


class TestSearchAnalyticsAlert:
    def test_defaults(self) -> None:
        a = SearchAnalyticsAlert(id="a1", metric_name="avg_duration_ms")
        assert a.id == "a1"
        assert a.acknowledged is False
        assert a.severity == "warning"


class TestSearchFunnel:
    def test_defaults(self) -> None:
        f = SearchFunnel(id="f1", name="Test Funnel")
        assert f.id == "f1"
        assert f.steps == ()


class TestSearchFunnelStep:
    def test_defaults(self) -> None:
        s = SearchFunnelStep(name="Step 1", order=1)
        assert s.name == "Step 1"
        assert s.order == 1


class TestSearchFunnelAnalysis:
    def test_defaults(self) -> None:
        fa = SearchFunnelAnalysis(funnel_id="f1")
        assert fa.funnel_id == "f1"
        assert fa.total_entries == 0


class TestSearchAbandonmentAnalysis:
    def test_defaults(self) -> None:
        aa = SearchAbandonmentAnalysis()
        assert aa.total_sessions == 0
        assert aa.abandoned_sessions == 0


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestSearchAnalyticsConfigUpdated:
    def test_event_type(self) -> None:
        e = SearchAnalyticsConfigUpdated()
        assert e.event_type == "eaip.search_analytics.config.updated"
        assert isinstance(e, DomainEvent)


class TestSearchQueryLogged:
    def test_event_type(self) -> None:
        e = SearchQueryLogged(query_id="q1")
        assert e.event_type == "eaip.search_analytics.query.logged"
        assert e.query_id == "q1"


class TestSearchMetricsCollected:
    def test_event_type(self) -> None:
        e = SearchMetricsCollected(period="last_24h", total_queries=100)
        assert e.event_type == "eaip.search_analytics.metrics.collected"
        assert e.total_queries == 100


class TestSearchPerformanceReportGenerated:
    def test_event_type(self) -> None:
        e = SearchPerformanceReportGenerated(report_id="r1")
        assert e.event_type == "eaip.search_analytics.performance_report.generated"


class TestSearchTrendComputed:
    def test_event_type(self) -> None:
        e = SearchTrendComputed(metric_name="avg_duration_ms")
        assert e.event_type == "eaip.search_analytics.trend.computed"


class TestSearchAnalyticsReportGenerated:
    def test_event_type(self) -> None:
        e = SearchAnalyticsReportGenerated(report_id="r1")
        assert e.event_type == "eaip.search_analytics.report.generated"


class TestSearchAnalyticsDashboardCreated:
    def test_event_type(self) -> None:
        e = SearchAnalyticsDashboardCreated(dashboard_id="d1")
        assert e.event_type == "eaip.search_analytics.dashboard.created"


class TestSearchAnalyticsDashboardUpdated:
    def test_event_type(self) -> None:
        e = SearchAnalyticsDashboardUpdated(dashboard_id="d1")
        assert e.event_type == "eaip.search_analytics.dashboard.updated"


class TestSearchPopularQueryIdentified:
    def test_event_type(self) -> None:
        e = SearchPopularQueryIdentified(query="test")
        assert e.event_type == "eaip.search_analytics.popular_query.identified"


class TestSearchZeroResultQueryIdentified:
    def test_event_type(self) -> None:
        e = SearchZeroResultQueryIdentified(query="none")
        assert e.event_type == "eaip.search_analytics.zero_result_query.identified"


class TestSearchClickThroughLogged:
    def test_event_type(self) -> None:
        e = SearchClickThroughLogged(query="test", result_id="r1")
        assert e.event_type == "eaip.search_analytics.click_through.logged"


class TestSearchSessionStarted:
    def test_event_type(self) -> None:
        e = SearchSessionStarted(session_id="s1")
        assert e.event_type == "eaip.search_analytics.session.started"


class TestSearchSessionCompleted:
    def test_event_type(self) -> None:
        e = SearchSessionCompleted(session_id="s1")
        assert e.event_type == "eaip.search_analytics.session.completed"


class TestSearchSessionAbandoned:
    def test_event_type(self) -> None:
        e = SearchSessionAbandoned(session_id="s1")
        assert e.event_type == "eaip.search_analytics.session.abandoned"


class TestSearchAnalyticsAlertTriggered:
    def test_event_type(self) -> None:
        e = SearchAnalyticsAlertTriggered(alert_id="a1", metric_name="test")
        assert e.event_type == "eaip.search_analytics.alert.triggered"


class TestSearchFunnelAnalysisCompleted:
    def test_event_type(self) -> None:
        e = SearchFunnelAnalysisCompleted(funnel_id="f1")
        assert e.event_type == "eaip.search_analytics.funnel_analysis.completed"


class TestSearchAbandonmentAnalysisCompleted:
    def test_event_type(self) -> None:
        e = SearchAbandonmentAnalysisCompleted()
        assert e.event_type == "eaip.search_analytics.abandonment_analysis.completed"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestSearchAnalyticsError:
    def test_is_eaip_error(self) -> None:
        err = SearchAnalyticsError("base error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_default_code_overrides(self) -> None:
        assert SearchAnalyticsConfigError("cfg").code == ErrorCode.CONFIGURATION_INVALID
        assert SearchAnalyticsQueryError("q").code == ErrorCode.VALIDATION_FAILED
        assert SearchAnalyticsReportError("r").code == ErrorCode.INTERNAL_ERROR
        assert SearchAnalyticsDashboardError("d").code == ErrorCode.NOT_FOUND
        assert SearchAnalyticsAlertError("a").code == ErrorCode.INTERNAL_ERROR
        assert SearchMetricsCollectionError("m").code == ErrorCode.INTERNAL_ERROR

    def test_custom_code(self) -> None:
        err = SearchAnalyticsError("custom", code=ErrorCode.RATE_LIMITED)
        assert err.code == ErrorCode.RATE_LIMITED


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TestSearchAnalyticsService:
    async def test_update_config(self) -> None:
        svc = SearchAnalyticsService()
        new_config = SearchAnalyticsConfig(retention_days=180)
        result = await svc.update_config(new_config)
        assert result.retention_days == 180
        assert svc.config.retention_days == 180

    async def test_log_query(self) -> None:
        svc = SearchAnalyticsService()
        log = await svc.log_query(query="test query", user_id="user1")
        assert log.query == "test query"
        assert log.user_id == "user1"
        assert log.id.startswith("q_")

    async def test_log_query_disabled(self) -> None:
        svc = SearchAnalyticsService(config=SearchAnalyticsConfig(logging_enabled=False))
        with pytest.raises(SearchAnalyticsConfigError):
            await svc.log_query(query="test")

    async def test_collect_metrics_empty(self) -> None:
        svc = SearchAnalyticsService()
        metrics = await svc.collect_metrics()
        assert metrics.total_queries == 0

    async def test_collect_metrics_with_data(self) -> None:
        svc = SearchAnalyticsService()
        await svc.log_query(query="q1", user_id="u1", duration_ms=10.0, result_count=5)
        await svc.log_query(query="q2", user_id="u2", duration_ms=20.0, result_count=0)
        await svc.log_query(query="q3", user_id="u1", duration_ms=30.0, result_count=3)

        metrics = await svc.collect_metrics(SearchMetricsPeriod.LAST_7D)
        assert metrics.total_queries == 3
        assert metrics.unique_users == 2
        assert metrics.zero_result_queries == 1

    async def test_generate_performance_report(self) -> None:
        svc = SearchAnalyticsService()
        await svc.log_query(query="test", result_count=5, duration_ms=15.0)
        report = await svc.generate_performance_report()
        assert report.metrics is not None
        assert report.avg_response_time_ms > 0

    async def test_compute_trend(self) -> None:
        svc = SearchAnalyticsService()
        for i in range(20):
            await svc.log_query(query=f"q{i}", duration_ms=10.0 + i)

        trend = await svc.compute_trend("avg_duration_ms", SearchTrendPeriod.DAILY)
        assert trend.metric_name == "avg_duration_ms"
        assert trend.data_points == 20

    async def test_generate_report(self) -> None:
        svc = SearchAnalyticsService()
        await svc.log_query(query="test", user_id="u1", duration_ms=5.0, result_count=10)
        report = await svc.generate_report("Test Report")
        assert report.name == "Test Report"
        assert report.metrics is not None
        assert report.performance is not None

    async def test_create_and_list_dashboards(self) -> None:
        svc = SearchAnalyticsService()
        d1 = await svc.create_dashboard("Dash 1", "First dashboard")
        d2 = await svc.create_dashboard("Dash 2")

        assert d1.name == "Dash 1"
        assert d2.name == "Dash 2"

        dashboards = await svc.list_dashboards()
        assert len(dashboards) == 2

    async def test_update_dashboard(self) -> None:
        svc = SearchAnalyticsService()
        d = await svc.create_dashboard("Original")
        updated = await svc.update_dashboard(d.id, name="Updated")
        assert updated.name == "Updated"

    async def test_update_dashboard_not_found(self) -> None:
        svc = SearchAnalyticsService()
        with pytest.raises(SearchAnalyticsReportError):
            await svc.update_dashboard("nonexistent", name="New")

    async def test_identify_popular_queries(self) -> None:
        svc = SearchAnalyticsService()
        config = SearchAnalyticsConfig(popular_query_threshold=2)
        svc = SearchAnalyticsService(config=config)

        for _ in range(3):
            await svc.log_query(query="popular", user_id="u1", duration_ms=10.0)

        popular = await svc.identify_popular_queries()
        assert len(popular) == 1
        assert popular[0].query == "popular"
        assert popular[0].count >= 3

    async def test_identify_zero_result_queries(self) -> None:
        svc = SearchAnalyticsService()
        await svc.log_query(query="no results", result_count=0, user_id="u1")
        await svc.log_query(query="no results", result_count=0, user_id="u2")
        await svc.log_query(query="has results", result_count=5)

        zero = await svc.identify_zero_result_queries()
        assert len(zero) == 1
        assert zero[0].query == "no results"
        assert zero[0].count == 2

    async def test_log_click_through(self) -> None:
        svc = SearchAnalyticsService()
        ct = await svc.log_click_through(
            query="test", result_id="r1", result_position=1, user_id="u1"
        )
        assert ct.query == "test"
        assert ct.result_id == "r1"

    async def test_session_lifecycle(self) -> None:
        svc = SearchAnalyticsService()
        session = await svc.start_session("s1", user_id="u1")
        assert session.status == SearchSessionStatus.ACTIVE

        completed = await svc.complete_session("s1")
        assert completed.status == SearchSessionStatus.COMPLETED

    async def test_abandon_session(self) -> None:
        svc = SearchAnalyticsService()
        await svc.start_session("s1", user_id="u1")
        abandoned = await svc.abandon_session("s1")
        assert abandoned.status == SearchSessionStatus.ABANDONED
        assert abandoned.total_duration_ms >= 0

    async def test_session_not_found(self) -> None:
        svc = SearchAnalyticsService()
        with pytest.raises(SearchAnalyticsReportError):
            await svc.complete_session("nonexistent")
        with pytest.raises(SearchAnalyticsReportError):
            await svc.abandon_session("nonexistent")

    async def test_create_and_check_alerts(self) -> None:
        svc = SearchAnalyticsService()
        alert = await svc.create_alert(
            metric_name="total_queries",
            threshold_value=5,
            operator="gt",
            severity="warning",
        )
        assert alert.metric_name == "total_queries"

        metrics = SearchMetrics(total_queries=10)
        triggered = await svc.check_alerts(metrics)
        assert len(triggered) == 1
        assert triggered[0].current_value == 10.0

    async def test_alert_not_triggered(self) -> None:
        svc = SearchAnalyticsService()
        await svc.create_alert("total_queries", 100, "gt")
        metrics = SearchMetrics(total_queries=10)
        triggered = await svc.check_alerts(metrics)
        assert len(triggered) == 0

    async def test_create_and_analyze_funnel(self) -> None:
        svc = SearchAnalyticsService()
        steps = [
            SearchFunnelStep(name="Search", order=1, description="User searches"),
            SearchFunnelStep(name="Click", order=2, description="User clicks result"),
        ]
        funnel = await svc.create_funnel("Search Funnel", steps)
        assert funnel.name == "Search Funnel"
        assert len(funnel.steps) == 2

        await svc.log_query(query="test", source="web")
        analysis = await svc.analyze_funnel(funnel.id)
        assert analysis.total_entries >= 1

    async def test_analyze_funnel_not_found(self) -> None:
        svc = SearchAnalyticsService()
        with pytest.raises(SearchAnalyticsReportError):
            await svc.analyze_funnel("nonexistent")

    async def test_analyze_abandonment(self) -> None:
        svc = SearchAnalyticsService()
        await svc.start_session("s1", user_id="u1")
        await svc.start_session("s2", user_id="u2")
        await svc.abandon_session("s1")

        analysis = await svc.analyze_abandonment()
        assert analysis.total_sessions >= 2
        assert analysis.abandoned_sessions >= 1
        assert analysis.abandonment_rate > 0

    async def test_get_dashboard(self) -> None:
        svc = SearchAnalyticsService()
        d = await svc.create_dashboard("Test")
        fetched = await svc.get_dashboard(d.id)
        assert fetched.id == d.id

    async def test_get_dashboard_not_found(self) -> None:
        svc = SearchAnalyticsService()
        with pytest.raises(SearchAnalyticsReportError):
            await svc.get_dashboard("nonexistent")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestSearchAnalyticsHealthCheck:
    async def test_check_healthy(self) -> None:
        hc = SearchAnalyticsHealthCheck(query_log_count=5)
        report = await hc.check()
        assert report.component == "search_analytics"
        assert report.status == HealthStatus.HEALTHY
        assert report.details["query_log_count"] == 5

    async def test_name(self) -> None:
        hc = SearchAnalyticsHealthCheck()
        assert hc.name == "search_analytics"


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestSearchAnalyticsRuntimeModule:
    async def test_initialization(self) -> None:
        module = SearchAnalyticsRuntimeModule()
        assert module.name == "search_analytics"
        assert module.service is not None

    async def test_custom_service(self) -> None:
        svc = SearchAnalyticsService()
        module = SearchAnalyticsRuntimeModule(service=svc)
        assert module.service is svc

    async def test_start_stop(self) -> None:
        module = SearchAnalyticsRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        kernel.platform.capabilities.register = MagicMock()

        await module.start(kernel)
        assert module.startup_duration >= 0
        kernel.platform.health.register.assert_called_once()
        kernel.platform.capabilities.register.assert_called_once()

        await module.stop(kernel)

    async def test_start_without_kernel(self) -> None:
        module = SearchAnalyticsRuntimeModule()
        await module.start()
        assert module.startup_duration >= 0

    async def test_register_with_runtime(self) -> None:
        module = SearchAnalyticsRuntimeModule()
        await module.register_with_runtime()
