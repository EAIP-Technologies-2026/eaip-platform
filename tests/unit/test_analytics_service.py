"""Tests for AnalyticsService."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from eaip.analytics.exceptions import MetricNotFoundError
from eaip.analytics.models import AggregationType, AnalyticsConfig, MetricDefinition, MetricType
from eaip.analytics.service import AnalyticsService


class TestAnalyticsService:
    @pytest.fixture
    def service(self) -> AnalyticsService:
        svc = AnalyticsService()
        return svc

    @pytest.fixture
    async def seeded_service(self) -> AnalyticsService:
        svc = AnalyticsService()
        m1 = MetricDefinition(id="m1", name="Requests", type=MetricType.COUNTER, unit="count")
        m2 = MetricDefinition(id="m2", name="Latency", type=MetricType.TIMER, unit="ms", aggregation=AggregationType.AVG)
        await svc.register_metric(m1)
        await svc.register_metric(m2)
        return svc

    class TestRegisterMetric:
        async def test_registers_new_metric(self, service: AnalyticsService) -> None:
            m = MetricDefinition(id="m1", name="Test")
            result = await service.register_metric(m)
            assert result.id == "m1"
            assert await service.get_metric("m1") is m

        async def test_overwrites_existing(self, service: AnalyticsService) -> None:
            m1 = MetricDefinition(id="m1", name="Old")
            m2 = MetricDefinition(id="m1", name="New", description="updated")
            await service.register_metric(m1)
            await service.register_metric(m2)
            result = await service.get_metric("m1")
            assert result.name == "New"

    class TestGetMetric:
        async def test_returns_metric(self, seeded_service: AnalyticsService) -> None:
            m = await seeded_service.get_metric("m1")
            assert m.id == "m1"
            assert m.name == "Requests"

        async def test_raises_on_missing(self, service: AnalyticsService) -> None:
            with pytest.raises(MetricNotFoundError):
                await service.get_metric("nonexistent")

    class TestListMetrics:
        async def test_empty_when_none_registered(self, service: AnalyticsService) -> None:
            assert await service.list_metrics() == []

        async def test_returns_all(self, seeded_service: AnalyticsService) -> None:
            metrics = await seeded_service.list_metrics()
            assert len(metrics) == 2

        async def test_filters_by_tags(self, service: AnalyticsService) -> None:
            m1 = MetricDefinition(id="m1", name="A", tags=("prod",))
            m2 = MetricDefinition(id="m2", name="B", tags=("dev",))
            await service.register_metric(m1)
            await service.register_metric(m2)
            result = await service.list_metrics(tags=("prod",))
            assert len(result) == 1
            assert result[0].id == "m1"

    class TestRecordMetric:
        async def test_records_point(self, seeded_service: AnalyticsService) -> None:
            point = await seeded_service.record_metric("m1", 42.0, {"env": "test"})
            assert point.metric_id == "m1"
            assert point.value == 42.0
            assert point.tags == {"env": "test"}

        async def test_raises_on_unregistered(self, service: AnalyticsService) -> None:
            with pytest.raises(MetricNotFoundError):
                await service.record_metric("unknown", 1.0)

        async def test_disabled_metric_records_with_warning(self, seeded_service: AnalyticsService) -> None:
            m = await seeded_service.get_metric("m1")
            disabled = MetricDefinition(id="m1", name=m.name, enabled=False)
            await seeded_service.register_metric(disabled)
            point = await seeded_service.record_metric("m1", 10.0)
            assert point.value == 10.0

    class TestQueryTimeSeries:
        async def test_returns_empty_when_no_points(self, seeded_service: AnalyticsService) -> None:
            now = datetime.now(timezone.utc)
            result = await seeded_service.query_time_series("m1", now, now + timedelta(hours=1))
            assert len(result.points) == 0

        async def test_returns_aggregated_points(self, seeded_service: AnalyticsService) -> None:
            now = datetime.now(timezone.utc)
            await seeded_service.record_metric("m1", 10.0)
            await seeded_service.record_metric("m1", 20.0)
            start = now - timedelta(minutes=5)
            end = now + timedelta(minutes=5)
            result = await seeded_service.query_time_series("m1", start, end, interval=3600.0, aggregation=AggregationType.SUM)
            assert len(result.points) >= 1
            assert result.points[0].value >= 30.0

        async def test_raises_on_missing_metric(self, service: AnalyticsService) -> None:
            now = datetime.now(timezone.utc)
            with pytest.raises(MetricNotFoundError):
                await service.query_time_series("unknown", now, now)

    class TestGenerateReport:
        async def test_generates_empty_report(self, service: AnalyticsService) -> None:
            now = datetime.now(timezone.utc)
            report = await service.generate_report([], (now, now))
            assert report.results == {}

        async def test_generates_report_with_metrics(self, seeded_service: AnalyticsService) -> None:
            await seeded_service.record_metric("m1", 100.0)
            await seeded_service.record_metric("m2", 200.0)
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=1)
            report = await seeded_service.generate_report(["m1", "m2"], (start, now))
            assert len(report.metric_ids) == 2
            assert "m1" in report.results
            assert "m2" in report.results

        async def test_skips_missing_metrics(self, seeded_service: AnalyticsService) -> None:
            now = datetime.now(timezone.utc)
            report = await seeded_service.generate_report(["m1", "nonexistent"], (now, now))
            assert "m1" in report.results
            assert "nonexistent" not in report.results

    class TestConfig:
        def test_default_config(self) -> None:
            svc = AnalyticsService()
            assert svc.config.retention_days == 90

        def test_custom_config(self) -> None:
            cfg = AnalyticsConfig(retention_days=30)
            svc = AnalyticsService(config=cfg)
            assert svc.config.retention_days == 30
