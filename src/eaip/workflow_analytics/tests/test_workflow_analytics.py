"""Tests for workflow_analytics — models, events, exceptions, service, health, integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.events.event import DomainEvent
from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.health.checks import HealthStatus
from eaip.workflow_analytics.events import (
    BottleneckDetected,
    PerformanceTrendComputed,
    WorkflowAnalyticsConfigUpdated,
    WorkflowAnalyticsReportGenerated,
    WorkflowMetricsCollected,
    WorkflowSlaComplianceComputed,
    WorkflowThroughputAnalyzed,
)
from eaip.workflow_analytics.exceptions import (
    WorkflowAnalyticsConfigError,
    WorkflowAnalyticsDataNotFoundError,
    WorkflowAnalyticsError,
    WorkflowAnalyticsQueryError,
    WorkflowAnalyticsReportError,
)
from eaip.workflow_analytics.health import WorkflowAnalyticsHealthCheck
from eaip.workflow_analytics.integration import WorkflowAnalyticsRuntimeModule
from eaip.workflow_analytics.models import (
    AnalyticsPeriod,
    BottleneckReport,
    PerformanceTrend,
    ThroughputAnalysis,
    WorkflowAnalyticsConfig,
    WorkflowAnalyticsReport,
    WorkflowMetrics,
)
from eaip.workflow_analytics.service import WorkflowAnalyticsService

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestAnalyticsPeriod:
    def test_values(self) -> None:
        assert AnalyticsPeriod.LAST_HOUR.value == "last_hour"
        assert AnalyticsPeriod.LAST_24H.value == "last_24h"
        assert AnalyticsPeriod.LAST_7D.value == "last_7d"
        assert AnalyticsPeriod.LAST_30D.value == "last_30d"
        assert AnalyticsPeriod.CUSTOM.value == "custom"


class TestWorkflowMetrics:
    def test_defaults(self) -> None:
        m = WorkflowMetrics(workflow_id="wf1")
        assert m.workflow_id == "wf1"
        assert m.total_executions == 0
        assert m.succeeded == 0
        assert m.failed == 0
        assert m.avg_duration_seconds == 0.0

    def test_with_values(self) -> None:
        m = WorkflowMetrics(
            workflow_id="wf1",
            workflow_name="test-workflow",
            total_executions=100,
            succeeded=95,
            failed=5,
            avg_duration_seconds=30.5,
        )
        assert m.total_executions == 100
        assert m.succeeded == 95
        assert m.failed == 5

    def test_frozen(self) -> None:
        m = WorkflowMetrics(workflow_id="wf1")
        with pytest.raises((ValueError, TypeError)):
            m.workflow_id = "wf2"


class TestThroughputAnalysis:
    def test_defaults(self) -> None:
        a = ThroughputAnalysis(workflow_id="wf1", period=AnalyticsPeriod.LAST_24H)
        assert a.total_executions == 0
        assert a.executions_per_hour == 0.0

    def test_with_values(self) -> None:
        a = ThroughputAnalysis(
            workflow_id="wf1",
            period=AnalyticsPeriod.LAST_24H,
            total_executions=500,
            executions_per_hour=20.83,
            peak_hour="14:00",
            peak_executions=50,
        )
        assert a.total_executions == 500
        assert a.peak_hour == "14:00"


class TestBottleneckReport:
    def test_defaults(self) -> None:
        b = BottleneckReport(workflow_id="wf1")
        assert b.bottleneck_type == ""
        assert b.severity == "medium"

    def test_with_values(self) -> None:
        b = BottleneckReport(
            workflow_id="wf1",
            bottleneck_type="high_failure_rate",
            description="High failure rate detected",
            severity="high",
        )
        assert b.severity == "high"


class TestPerformanceTrend:
    def test_defaults(self) -> None:
        t = PerformanceTrend(workflow_id="wf1")
        assert t.direction == "stable"
        assert t.change_percent == 0.0

    def test_with_values(self) -> None:
        t = PerformanceTrend(
            workflow_id="wf1",
            metric_name="avg_duration",
            direction="degrading",
            change_percent=15.5,
            confidence=0.9,
        )
        assert t.change_percent == 15.5


class TestWorkflowAnalyticsReport:
    def test_defaults(self) -> None:
        r = WorkflowAnalyticsReport(id="r1", workflow_id="wf1")
        assert r.period == AnalyticsPeriod.LAST_24H
        assert r.sla_compliance_pct == 0.0

    def test_with_values(self) -> None:
        r = WorkflowAnalyticsReport(
            id="r1",
            workflow_id="wf1",
            sla_compliance_pct=98.5,
        )
        assert r.sla_compliance_pct == 98.5


class TestWorkflowAnalyticsConfig:
    def test_defaults(self) -> None:
        c = WorkflowAnalyticsConfig()
        assert c.enabled is True
        assert c.retention_days == 90
        assert c.enable_bottleneck_detection is True

    def test_custom_values(self) -> None:
        c = WorkflowAnalyticsConfig(enabled=False, retention_days=30)
        assert c.enabled is False
        assert c.retention_days == 30

    def test_frozen(self) -> None:
        c = WorkflowAnalyticsConfig()
        with pytest.raises((ValueError, TypeError)):
            c.enabled = False


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestWorkflowMetricsCollected:
    def test_defaults(self) -> None:
        e = WorkflowMetricsCollected(workflow_id="wf1")
        assert e.event_type == "eaip.workflow_analytics.metrics.collected"
        assert isinstance(e, DomainEvent)
        assert e.total_executions == 0

    def test_with_values(self) -> None:
        e = WorkflowMetricsCollected(
            workflow_id="wf1", total_executions=100, succeeded=95, failed=5
        )
        assert e.total_executions == 100

    def test_frozen(self) -> None:
        e = WorkflowMetricsCollected(workflow_id="wf1")
        with pytest.raises((ValueError, TypeError)):
            e.workflow_id = "wf2"


class TestWorkflowAnalyticsReportGenerated:
    def test_defaults(self) -> None:
        e = WorkflowAnalyticsReportGenerated(report_id="r1", workflow_id="wf1")
        assert e.event_type == "eaip.workflow_analytics.report.generated"

    def test_with_values(self) -> None:
        e = WorkflowAnalyticsReportGenerated(report_id="r1", workflow_id="wf1", period="last_24h")
        assert e.period == "last_24h"


class TestBottleneckDetected:
    def test_defaults(self) -> None:
        e = BottleneckDetected(workflow_id="wf1")
        assert e.event_type == "eaip.workflow_analytics.bottleneck.detected"
        assert e.severity == "medium"

    def test_with_values(self) -> None:
        e = BottleneckDetected(
            workflow_id="wf1",
            bottleneck_type="high_failure_rate",
            severity="high",
            avg_wait_time_seconds=45.0,
        )
        assert e.avg_wait_time_seconds == 45.0


class TestPerformanceTrendComputed:
    def test_defaults(self) -> None:
        e = PerformanceTrendComputed(workflow_id="wf1")
        assert e.event_type == "eaip.workflow_analytics.performance.trend.computed"
        assert e.direction == "stable"

    def test_with_values(self) -> None:
        e = PerformanceTrendComputed(
            workflow_id="wf1",
            metric_name="avg_duration",
            direction="degrading",
            change_percent=10.0,
        )
        assert e.change_percent == 10.0


class TestWorkflowThroughputAnalyzed:
    def test_defaults(self) -> None:
        e = WorkflowThroughputAnalyzed(workflow_id="wf1")
        assert e.event_type == "eaip.workflow_analytics.throughput.analyzed"

    def test_with_values(self) -> None:
        e = WorkflowThroughputAnalyzed(
            workflow_id="wf1", total_executions=500, executions_per_hour=20.83
        )
        assert e.executions_per_hour == 20.83


class TestWorkflowSlaComplianceComputed:
    def test_defaults(self) -> None:
        e = WorkflowSlaComplianceComputed(workflow_id="wf1")
        assert e.event_type == "eaip.workflow_analytics.sla.compliance.computed"

    def test_with_values(self) -> None:
        e = WorkflowSlaComplianceComputed(
            workflow_id="wf1", compliance_pct=99.5, sla_threshold_seconds=3600.0
        )
        assert e.compliance_pct == 99.5


class TestWorkflowAnalyticsConfigUpdated:
    def test_defaults(self) -> None:
        e = WorkflowAnalyticsConfigUpdated()
        assert e.event_type == "eaip.workflow_analytics.config.updated"

    def test_with_values(self) -> None:
        e = WorkflowAnalyticsConfigUpdated(changes={"enabled": False})
        assert e.changes == {"enabled": False}

    def test_frozen(self) -> None:
        e = WorkflowAnalyticsConfigUpdated()
        with pytest.raises((ValueError, TypeError)):
            e.changes = {"enabled": True}


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [
            WorkflowMetricsCollected,
            WorkflowAnalyticsReportGenerated,
            BottleneckDetected,
            PerformanceTrendComputed,
            WorkflowThroughputAnalyzed,
            WorkflowSlaComplianceComputed,
            WorkflowAnalyticsConfigUpdated,
        ]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestWorkflowAnalyticsError:
    def test_base_exception(self) -> None:
        err = WorkflowAnalyticsError("analytics error")
        assert str(err) == "analytics error"
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert isinstance(err, EAIPError)


class TestWorkflowAnalyticsConfigError:
    def test_default_code(self) -> None:
        err = WorkflowAnalyticsConfigError("invalid config")
        assert err.code == ErrorCode.CONFIGURATION_INVALID

    def test_inheritance(self) -> None:
        err = WorkflowAnalyticsConfigError("invalid config")
        assert isinstance(err, WorkflowAnalyticsError)


class TestWorkflowAnalyticsReportError:
    def test_default_code(self) -> None:
        err = WorkflowAnalyticsReportError("report failed")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_message(self) -> None:
        err = WorkflowAnalyticsReportError("report generation failed")
        assert str(err) == "report generation failed"


class TestWorkflowAnalyticsQueryError:
    def test_default_code(self) -> None:
        err = WorkflowAnalyticsQueryError("query failed")
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestWorkflowAnalyticsDataNotFoundError:
    def test_default_code(self) -> None:
        err = WorkflowAnalyticsDataNotFoundError("wf1")
        assert err.code == ErrorCode.NOT_FOUND

    def test_message(self) -> None:
        err = WorkflowAnalyticsDataNotFoundError("wf1")
        assert "wf1" in str(err)
        assert err.workflow_id == "wf1"

    def test_inheritance(self) -> None:
        err = WorkflowAnalyticsDataNotFoundError("wf1")
        assert isinstance(err, WorkflowAnalyticsError)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TestWorkflowAnalyticsService:
    @pytest.fixture
    def svc(self) -> WorkflowAnalyticsService:
        return WorkflowAnalyticsService()

    @pytest.fixture
    def sample_metrics(self) -> WorkflowMetrics:
        return WorkflowMetrics(
            workflow_id="wf1",
            workflow_name="test-workflow",
            total_executions=100,
            succeeded=95,
            failed=5,
            avg_duration_seconds=30.0,
        )

    class TestRecordMetrics:
        async def test_records_metrics(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            result = await svc.record_metrics(sample_metrics)
            assert result.workflow_id == "wf1"
            assert result.total_executions == 100

        async def test_stores_metrics(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            stored = await svc.get_metrics("wf1")
            assert len(stored) == 1

    class TestGetMetrics:
        async def test_returns_metrics(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            result = await svc.get_metrics("wf1")
            assert len(result) == 1
            assert result[0].workflow_id == "wf1"

        async def test_raises_on_missing(self, svc: WorkflowAnalyticsService) -> None:
            with pytest.raises(WorkflowAnalyticsDataNotFoundError):
                await svc.get_metrics("nonexistent")

    class TestAnalyzeThroughput:
        async def test_returns_analysis(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            analysis = await svc.analyze_throughput("wf1")
            assert isinstance(analysis, ThroughputAnalysis)
            assert analysis.total_executions == 100

        async def test_raises_on_missing(self, svc: WorkflowAnalyticsService) -> None:
            with pytest.raises(WorkflowAnalyticsDataNotFoundError):
                await svc.analyze_throughput("nonexistent")

    class TestDetectBottlenecks:
        async def test_no_bottlenecks_when_healthy(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            bottlenecks = await svc.detect_bottlenecks("wf1")
            assert len(bottlenecks) == 0

        async def test_detects_high_failure_rate(self, svc: WorkflowAnalyticsService) -> None:
            bad_metrics = WorkflowMetrics(
                workflow_id="wf1",
                total_executions=100,
                succeeded=50,
                failed=50,
                avg_duration_seconds=10.0,
            )
            await svc.record_metrics(bad_metrics)
            bottlenecks = await svc.detect_bottlenecks("wf1")
            assert any(b.bottleneck_type == "high_failure_rate" for b in bottlenecks)

        async def test_detects_sla_violation(self, svc: WorkflowAnalyticsService) -> None:
            slow_metrics = WorkflowMetrics(
                workflow_id="wf1",
                total_executions=10,
                succeeded=10,
                failed=0,
                avg_duration_seconds=7200.0,
            )
            await svc.record_metrics(slow_metrics)
            bottlenecks = await svc.detect_bottlenecks("wf1")
            assert any(b.bottleneck_type == "sla_violation" for b in bottlenecks)

    class TestComputeTrends:
        async def test_returns_empty_with_one_datapoint(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            trends = await svc.compute_trends("wf1")
            assert len(trends) == 0

        async def test_returns_trend_with_multiple_points(
            self, svc: WorkflowAnalyticsService
        ) -> None:
            for i in range(4):
                m = WorkflowMetrics(
                    workflow_id="wf1",
                    total_executions=100,
                    succeeded=95,
                    failed=5,
                    avg_duration_seconds=float(30 + i * 5),
                )
                await svc.record_metrics(m)
            trends = await svc.compute_trends("wf1")
            assert len(trends) == 1
            assert trends[0].metric_name == "avg_duration_seconds"

    class TestComputeSlaCompliance:
        async def test_returns_100_with_no_metrics(self, svc: WorkflowAnalyticsService) -> None:
            with pytest.raises(WorkflowAnalyticsDataNotFoundError):
                await svc.compute_sla_compliance("nonexistent")

        async def test_computes_compliance(self, svc: WorkflowAnalyticsService) -> None:
            m = WorkflowMetrics(
                workflow_id="wf1",
                total_executions=10,
                succeeded=10,
                failed=0,
                avg_duration_seconds=30.0,
            )
            await svc.record_metrics(m)
            pct = await svc.compute_sla_compliance("wf1")
            assert pct == 100.0

    class TestGenerateReport:
        async def test_generates_report(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            report = await svc.generate_report("wf1")
            assert isinstance(report, WorkflowAnalyticsReport)
            assert report.workflow_id == "wf1"

        async def test_raises_on_no_data(self, svc: WorkflowAnalyticsService) -> None:
            with pytest.raises(WorkflowAnalyticsQueryError):
                await svc.generate_report("nonexistent")

    class TestGetReport:
        async def test_returns_report(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            report = await svc.generate_report("wf1")
            fetched = await svc.get_report(report.id)
            assert fetched.id == report.id

        async def test_raises_on_missing(self, svc: WorkflowAnalyticsService) -> None:
            with pytest.raises(WorkflowAnalyticsDataNotFoundError):
                await svc.get_report("nonexistent")

    class TestListReports:
        async def test_returns_reports(
            self, svc: WorkflowAnalyticsService, sample_metrics: WorkflowMetrics
        ) -> None:
            await svc.record_metrics(sample_metrics)
            await svc.generate_report("wf1")
            reports = await svc.list_reports()
            assert len(reports) == 1

        async def test_filters_by_workflow(self, svc: WorkflowAnalyticsService) -> None:
            m1 = WorkflowMetrics(workflow_id="wf1", total_executions=10, succeeded=10, failed=0)
            m2 = WorkflowMetrics(workflow_id="wf2", total_executions=20, succeeded=20, failed=0)
            await svc.record_metrics(m1)
            await svc.record_metrics(m2)
            await svc.generate_report("wf1")
            await svc.generate_report("wf2")
            reports = await svc.list_reports(workflow_id="wf1")
            assert len(reports) == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = WorkflowAnalyticsService()
            assert svc.config.enabled is True
            assert svc.config.retention_days == 90

        def test_custom_config(self) -> None:
            cfg = WorkflowAnalyticsConfig(enabled=False, retention_days=30)
            svc = WorkflowAnalyticsService(config=cfg)
            assert svc.config.enabled is False
            assert svc.config.retention_days == 30

        async def test_update_config(self, svc: WorkflowAnalyticsService) -> None:
            new_cfg = WorkflowAnalyticsConfig(enabled=False)
            result = await svc.update_config(new_cfg)
            assert result.enabled is False
            assert svc.config.enabled is False


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestWorkflowAnalyticsHealthCheck:
    @pytest.fixture
    def check(self) -> WorkflowAnalyticsHealthCheck:
        return WorkflowAnalyticsHealthCheck()

    def test_name(self, check: WorkflowAnalyticsHealthCheck) -> None:
        assert check.name == "eaip.workflow_analytics"

    async def test_healthy(self, check: WorkflowAnalyticsHealthCheck) -> None:
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "WorkflowAnalyticsService"

    async def test_degraded_when_disabled(self) -> None:
        cfg = WorkflowAnalyticsConfig(enabled=False)
        svc = WorkflowAnalyticsService(config=cfg)
        check = WorkflowAnalyticsHealthCheck(service=svc)
        report = await check.check()
        assert report.status == HealthStatus.DEGRADED


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestWorkflowAnalyticsRuntimeModule:
    @pytest.fixture
    def module(self) -> WorkflowAnalyticsRuntimeModule:
        return WorkflowAnalyticsRuntimeModule()

    def test_name(self, module: WorkflowAnalyticsRuntimeModule) -> None:
        assert module.name == "workflow_analytics"

    def test_service_property(self, module: WorkflowAnalyticsRuntimeModule) -> None:
        assert isinstance(module.service, WorkflowAnalyticsService)

    async def test_start_stop(self, module: WorkflowAnalyticsRuntimeModule) -> None:
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        kernel.platform.capabilities.register = MagicMock()
        kernel.register_module = MagicMock()

        await module.start(kernel)
        kernel.platform.health.register.assert_called_once()
        assert kernel.platform.capabilities.register.call_count == 2
        kernel.register_module.assert_called_once_with("workflow_analytics.service", module.service)

        await module.stop(kernel)
