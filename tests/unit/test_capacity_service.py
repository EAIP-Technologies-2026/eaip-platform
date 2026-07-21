"""Tests for CapacityAnalyzer service."""

from __future__ import annotations

import pytest

from eaip.capacity.analyzer import CapacityAnalyzer
from eaip.capacity.exceptions import CapacityError, ResourceNotFoundError
from eaip.capacity.models import CapacityConfig, CapacityReport, ResourceMetric


class TestCapacityAnalyzer:
    @pytest.fixture
    def analyzer(self) -> CapacityAnalyzer:
        return CapacityAnalyzer()

    @pytest.fixture
    def sample_metric(self) -> ResourceMetric:
        return ResourceMetric(
            id="m1",
            resource_id="res1",
            metric_name="cpu_usage",
            value=75.0,
        )

    class TestRecordMetric:
        async def test_record_metric(
            self, analyzer: CapacityAnalyzer, sample_metric: ResourceMetric
        ) -> None:
            result = await analyzer.record_metric(sample_metric)
            assert result.id == "m1"
            assert result.value == 75.0

        async def test_get_metrics(
            self, analyzer: CapacityAnalyzer, sample_metric: ResourceMetric
        ) -> None:
            await analyzer.record_metric(sample_metric)
            metrics = await analyzer.get_metrics("res1")
            assert len(metrics) == 1

        async def test_get_metrics_by_name(
            self, analyzer: CapacityAnalyzer, sample_metric: ResourceMetric
        ) -> None:
            await analyzer.record_metric(sample_metric)
            m2 = ResourceMetric(id="m2", resource_id="res1", metric_name="memory_usage", value=50.0)
            await analyzer.record_metric(m2)
            metrics = await analyzer.get_metrics("res1", metric_name="cpu_usage")
            assert len(metrics) == 1
            assert metrics[0].metric_name == "cpu_usage"

    class TestGetResourceIds:
        async def test_get_resource_ids(
            self, analyzer: CapacityAnalyzer, sample_metric: ResourceMetric
        ) -> None:
            await analyzer.record_metric(sample_metric)
            ids = await analyzer.get_resource_ids()
            assert ids == ["res1"]

    class TestGenerateReport:
        async def test_generate_report_with_metrics(
            self, analyzer: CapacityAnalyzer, sample_metric: ResourceMetric
        ) -> None:
            await analyzer.record_metric(sample_metric)
            report = await analyzer.generate_report("res1")
            assert report.resource_id == "res1"
            assert report.current_usage == 75.0
            assert report.predicted_usage > 0
            assert report.recommended_capacity > 0
            assert report.confidence > 0

        async def test_generate_report_no_metrics(self, analyzer: CapacityAnalyzer) -> None:
            report = await analyzer.generate_report("res1")
            assert report.resource_id == "res1"
            assert report.current_usage == 0.0

    class TestGetReport:
        async def test_get_report(
            self, analyzer: CapacityAnalyzer, sample_metric: ResourceMetric
        ) -> None:
            await analyzer.record_metric(sample_metric)
            report = await analyzer.generate_report("res1")
            result = await analyzer.get_report(report.id)
            assert result.resource_id == "res1"

        async def test_get_report_not_found(self, analyzer: CapacityAnalyzer) -> None:
            with pytest.raises(ResourceNotFoundError):
                await analyzer.get_report("nonexistent")

    class TestListReports:
        async def test_list_all(
            self, analyzer: CapacityAnalyzer, sample_metric: ResourceMetric
        ) -> None:
            await analyzer.record_metric(sample_metric)
            await analyzer.generate_report("res1")
            reports = await analyzer.list_reports()
            assert len(reports) == 1

        async def test_list_by_resource(self, analyzer: CapacityAnalyzer) -> None:
            m1 = ResourceMetric(id="m1", resource_id="res1", metric_name="cpu", value=50.0)
            m2 = ResourceMetric(id="m2", resource_id="res2", metric_name="cpu", value=60.0)
            await analyzer.record_metric(m1)
            await analyzer.record_metric(m2)
            await analyzer.generate_report("res1")
            await analyzer.generate_report("res2")
            reports = await analyzer.list_reports("res1")
            assert len(reports) == 1
            assert reports[0].resource_id == "res1"

    class TestThresholdBreach:
        async def test_warning_threshold(self, analyzer: CapacityAnalyzer) -> None:
            config = CapacityConfig(threshold_warning=80.0, threshold_critical=95.0)
            a = CapacityAnalyzer(config=config)
            metric = ResourceMetric(id="m1", resource_id="res1", metric_name="cpu", value=85.0)
            await a.record_metric(metric)

        async def test_critical_threshold(self, analyzer: CapacityAnalyzer) -> None:
            config = CapacityConfig(threshold_warning=80.0, threshold_critical=95.0)
            a = CapacityAnalyzer(config=config)
            metric = ResourceMetric(id="m1", resource_id="res1", metric_name="cpu", value=98.0)
            await a.record_metric(metric)

    class TestConfig:
        def test_default_config(self) -> None:
            a = CapacityAnalyzer()
            assert a.config.threshold_warning == 80.0
            assert a.config.threshold_critical == 95.0

        def test_custom_config(self) -> None:
            config = CapacityConfig(threshold_warning=70.0, prediction_window_hours=48)
            a = CapacityAnalyzer(config=config)
            assert a.config.threshold_warning == 70.0
            assert a.config.prediction_window_hours == 48
