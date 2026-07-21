"""Tests for :mod:`eaip.perf.regression`."""

from __future__ import annotations

import pytest

from eaip.perf.benchmarks import BenchmarkEngine
from eaip.perf.exceptions import RegressionNotFoundError
from eaip.perf.models import (
    BenchmarkDefinition,
    BenchmarkRun,
    BenchmarkRunStatus,
    MetricType,
    RegressionDirection,
    RegressionSeverity,
    RegressionStatus,
)
from eaip.perf.regression import RegressionDetector

BenchmarkEngine.__test__ = False
RegressionDetector.__test__ = False
BenchmarkDefinition.__test__ = False
BenchmarkRun.__test__ = False
RegressionNotFoundError.__test__ = False
RegressionDirection.__test__ = False
RegressionSeverity.__test__ = False
RegressionStatus.__test__ = False


@pytest.fixture
def engine() -> BenchmarkEngine:
    eng = BenchmarkEngine()
    b = BenchmarkDefinition(
        id="b1", name="test", component="api", metric_type=MetricType.LATENCY, target_value=100.0
    )
    eng.create_benchmark(b)
    return eng


@pytest.fixture
def detector(engine: BenchmarkEngine) -> RegressionDetector:
    return RegressionDetector(engine=engine)


class TestBaseline:
    @pytest.mark.asyncio
    async def test_set_and_get_baseline(self, detector: RegressionDetector) -> None:
        run = BenchmarkRun(
            id="r1", benchmark_id="b1", status=BenchmarkRunStatus.COMPLETED, result_value=100.0
        )
        await detector.set_baseline("b1", run)
        baseline = await detector.get_baseline("b1")
        assert baseline is not None
        assert baseline.id == "r1"

    @pytest.mark.asyncio
    async def test_get_baseline_nonexistent(self, detector: RegressionDetector) -> None:
        baseline = await detector.get_baseline("nonexistent")
        assert baseline is None


class TestDetectRegression:
    @pytest.mark.asyncio
    async def test_detect_no_baseline(
        self, detector: RegressionDetector, engine: BenchmarkEngine
    ) -> None:
        run = await engine.run_benchmark("b1")
        regression = await detector.detect_regression("b1", run.id)
        assert regression is None

    @pytest.mark.asyncio
    async def test_detect_no_change(
        self, detector: RegressionDetector, engine: BenchmarkEngine
    ) -> None:
        baseline_run = await engine.run_benchmark("b1")
        await detector.set_baseline("b1", baseline_run)
        current_run = await engine.run_benchmark("b1")
        regression = await detector.detect_regression("b1", current_run.id)
        assert regression is not None

    @pytest.mark.asyncio
    async def test_detect_with_runs_unchanged(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=105.0)
        regression = await detector.detect_regression_with_runs(
            "b1", baseline, current, threshold_percent=10.0
        )
        assert regression is not None
        assert regression.direction is RegressionDirection.UNCHANGED
        assert regression.severity is RegressionSeverity.LOW

    @pytest.mark.asyncio
    async def test_detect_with_runs_regression(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=150.0)
        regression = await detector.detect_regression_with_runs(
            "b1", baseline, current, threshold_percent=10.0
        )
        assert regression is not None
        assert regression.direction is RegressionDirection.REGRESSION
        assert regression.change_percent == 50.0
        assert regression.severity is RegressionSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_detect_with_runs_improvement(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=200.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=50.0)
        regression = await detector.detect_regression_with_runs(
            "b1", baseline, current, threshold_percent=10.0
        )
        assert regression is not None
        assert regression.direction is RegressionDirection.IMPROVEMENT

    @pytest.mark.asyncio
    async def test_detect_with_runs_same_run(self, detector: RegressionDetector) -> None:
        run = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        regression = await detector.detect_regression_with_runs("b1", run, run)
        assert regression is None


class TestRegressionLifecycle:
    @pytest.mark.asyncio
    async def test_acknowledge(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=200.0)
        regression = await detector.detect_regression_with_runs("b1", baseline, current)
        assert regression is not None
        acknowledged = await detector.acknowledge_regression(regression.id)
        assert acknowledged.status is RegressionStatus.ACKNOWLEDGED

    @pytest.mark.asyncio
    async def test_resolve(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=200.0)
        regression = await detector.detect_regression_with_runs("b1", baseline, current)
        assert regression is not None
        resolved = await detector.resolve_regression(regression.id)
        assert resolved.status is RegressionStatus.RESOLVED

    @pytest.mark.asyncio
    async def test_false_positive(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=200.0)
        regression = await detector.detect_regression_with_runs("b1", baseline, current)
        assert regression is not None
        fp = await detector.mark_false_positive(regression.id)
        assert fp.status is RegressionStatus.FALSE_POSITIVE

    @pytest.mark.asyncio
    async def test_acknowledge_missing(self, detector: RegressionDetector) -> None:
        with pytest.raises(RegressionNotFoundError):
            await detector.acknowledge_regression("nonexistent")

    @pytest.mark.asyncio
    async def test_resolve_missing(self, detector: RegressionDetector) -> None:
        with pytest.raises(RegressionNotFoundError):
            await detector.resolve_regression("nonexistent")

    @pytest.mark.asyncio
    async def test_false_positive_missing(self, detector: RegressionDetector) -> None:
        with pytest.raises(RegressionNotFoundError):
            await detector.mark_false_positive("nonexistent")


class TestListRegressions:
    @pytest.mark.asyncio
    async def test_list_empty(self, detector: RegressionDetector) -> None:
        regressions = await detector.list_regressions()
        assert regressions == []

    @pytest.mark.asyncio
    async def test_list_all(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=200.0)
        await detector.detect_regression_with_runs("b1", baseline, current)
        regressions = await detector.list_regressions()
        assert len(regressions) == 1

    @pytest.mark.asyncio
    async def test_list_filter_by_status(self, detector: RegressionDetector) -> None:
        baseline = BenchmarkRun(id="r1", benchmark_id="b1", result_value=100.0)
        current = BenchmarkRun(id="r2", benchmark_id="b1", result_value=200.0)
        await detector.detect_regression_with_runs("b1", baseline, current)
        regressions = await detector.list_regressions(status="open")
        assert len(regressions) == 1
        regressions = await detector.list_regressions(status="resolved")
        assert len(regressions) == 0


class TestSeverityComputation:
    def test_low(self) -> None:
        assert RegressionDetector._compute_severity(5.0) is RegressionSeverity.LOW

    def test_medium(self) -> None:
        assert RegressionDetector._compute_severity(15.0) is RegressionSeverity.MEDIUM

    def test_high(self) -> None:
        assert RegressionDetector._compute_severity(30.0) is RegressionSeverity.HIGH

    def test_critical(self) -> None:
        assert RegressionDetector._compute_severity(50.0) is RegressionSeverity.CRITICAL
        assert RegressionDetector._compute_severity(75.0) is RegressionSeverity.CRITICAL
