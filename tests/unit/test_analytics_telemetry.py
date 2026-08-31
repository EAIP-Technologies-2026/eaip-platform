"""Tests for TelemetryCollector."""

from __future__ import annotations

import pytest

from eaip.analytics.models import MetricDefinition, MetricType
from eaip.analytics.service import AnalyticsService
from eaip.analytics.telemetry import TelemetryCollector


class TestTelemetryCollector:
    @pytest.fixture
    async def seeded_collector(self) -> TelemetryCollector:
        svc = AnalyticsService()
        for mid, name, mtype in [
            ("agents.active", "Active Agents", MetricType.GAUGE),
            ("agents.total", "Total Agents", MetricType.GAUGE),
            ("workflows.running", "Running Workflows", MetricType.GAUGE),
            ("sessions.active", "Active Sessions", MetricType.GAUGE),
            ("memory.usage_bytes", "Memory Usage", MetricType.GAUGE),
            ("platform.uptime_seconds", "Uptime", MetricType.COUNTER),
            ("platform.errors_total", "Errors", MetricType.COUNTER),
            ("platform.health_score", "Health Score", MetricType.GAUGE),
        ]:
            await svc.register_metric(MetricDefinition(id=mid, name=name, type=mtype))
        return TelemetryCollector(analytics_service=svc)

    class TestCollectOperationalMetrics:
        async def test_returns_dict(self, seeded_collector: TelemetryCollector) -> None:
            metrics = await seeded_collector.collect_operational_metrics()
            assert isinstance(metrics, dict)
            assert len(metrics) > 0

        async def test_includes_expected_keys(self, seeded_collector: TelemetryCollector) -> None:
            metrics = await seeded_collector.collect_operational_metrics()
            assert "agents.active" in metrics
            assert "agents.total" in metrics
            assert "workflows.running" in metrics
            assert "sessions.active" in metrics
            assert "memory.usage_bytes" in metrics

        async def test_records_default_values(self, seeded_collector: TelemetryCollector) -> None:
            metrics = await seeded_collector.collect_operational_metrics()
            assert all(v == 0.0 for v in metrics.values())

        async def test_handles_unregistered_metrics(self) -> None:
            svc = AnalyticsService()
            collector = TelemetryCollector(analytics_service=svc)
            metrics = await collector.collect_operational_metrics()
            assert isinstance(metrics, dict)

    class TestCollectPlatformMetrics:
        async def test_returns_dict(self, seeded_collector: TelemetryCollector) -> None:
            metrics = await seeded_collector.collect_platform_metrics()
            assert isinstance(metrics, dict)

        async def test_includes_expected_keys(self, seeded_collector: TelemetryCollector) -> None:
            metrics = await seeded_collector.collect_platform_metrics()
            assert "platform.uptime_seconds" in metrics
            assert "platform.errors_total" in metrics
            assert "platform.health_score" in metrics

        async def test_records_default_values(self, seeded_collector: TelemetryCollector) -> None:
            metrics = await seeded_collector.collect_platform_metrics()
            assert metrics["platform.health_score"] == 1.0

    class TestRecordMetricPoint:
        async def test_records_point(self, seeded_collector: TelemetryCollector) -> None:
            point = await seeded_collector.record_metric_point(
                "agents.active", 5.0, {"env": "prod"}
            )
            assert point.metric_id == "agents.active"
            assert point.value == 5.0
            assert point.tags == {"env": "prod"}

        async def test_uses_current_timestamp(self, seeded_collector: TelemetryCollector) -> None:
            point = await seeded_collector.record_metric_point("agents.active", 3.0)
            assert point.timestamp is not None

    class TestConstruction:
        def test_default_construction(self) -> None:
            collector = TelemetryCollector()
            assert isinstance(collector, TelemetryCollector)

        def test_with_service(self) -> None:
            svc = AnalyticsService()
            collector = TelemetryCollector(analytics_service=svc)
            assert collector is not None
