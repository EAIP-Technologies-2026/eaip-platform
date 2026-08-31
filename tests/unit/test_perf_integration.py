"""Tests for :mod:`eaip.perf.integration`."""

from __future__ import annotations

import pytest

from eaip.perf.benchmarks import BenchmarkEngine
from eaip.perf.health import PerfHealthCheck
from eaip.perf.integration import PerfRuntimeModule
from eaip.perf.load_testing import LoadTestOrchestrator
from eaip.perf.models import BenchmarkDefinition, MetricType
from eaip.perf.regression import RegressionDetector

BenchmarkEngine.__test__ = False
PerfHealthCheck.__test__ = False
LoadTestOrchestrator.__test__ = False
RegressionDetector.__test__ = False


class TestPerfRuntimeModule:
    def test_instantiation(self) -> None:
        module = PerfRuntimeModule()
        assert module.name == "perf"
        assert isinstance(module.engine, BenchmarkEngine)
        assert isinstance(module.orchestrator, LoadTestOrchestrator)
        assert isinstance(module.regression_detector, RegressionDetector)
        assert isinstance(module.health_check, PerfHealthCheck)

    def test_all_services_independent(self) -> None:
        module = PerfRuntimeModule()
        assert module.engine is not module.orchestrator
        assert module.engine is not module.regression_detector
        assert module.orchestrator is not module.regression_detector

    def test_regression_detector_has_engine(self) -> None:
        module = PerfRuntimeModule()
        assert module.regression_detector._engine is module.engine

    def test_health_check_references_services(self) -> None:
        module = PerfRuntimeModule()
        assert module.health_check._engine is module.engine
        assert module.health_check._orchestrator is module.orchestrator
        assert module.health_check._regression is module.regression_detector


class TestPerfHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        module = PerfRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "perf"
        assert report.status.value in ("healthy", "degraded")

    @pytest.mark.asyncio
    async def test_health_check_details(self) -> None:
        module = PerfRuntimeModule()
        report = await module.health_check.check()
        assert "benchmark_count" in report.details
        assert "scenario_count" in report.details
        assert "regression_count" in report.details

    @pytest.mark.asyncio
    async def test_health_check_with_benchmarks(self) -> None:
        module = PerfRuntimeModule()
        module.engine.create_benchmark(
            BenchmarkDefinition(
                id="b1",
                name="test",
                component="api",
                metric_type=MetricType.LATENCY,
                target_value=100.0,
            )
        )
        report = await module.health_check.check()
        assert report.details["benchmark_count"] >= 1
