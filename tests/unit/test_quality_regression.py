"""Tests for :mod:`eaip.quality.regression`."""

from __future__ import annotations

import pytest

from eaip.quality.exceptions import RegressionDetectionError
from eaip.quality.models import RegressionStatus, TestExecution, TestExecutionStatus

# Prevent pytest from collecting source classes as test classes
TestExecution.__test__ = False
TestExecutionStatus.__test__ = False
from eaip.quality.regression import RegressionDetector


class TestCreateBaseline:
    @pytest.mark.asyncio
    async def test_create_baseline(self) -> None:
        detector = RegressionDetector()
        detector._baselines["comp1"] = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED),
        ]
        result = await detector.create_baseline("comp1", ["e1"])
        assert "baseline_id" in result
        assert result["component"] == "comp1"

    @pytest.mark.asyncio
    async def test_create_baseline_no_executions(self) -> None:
        detector = RegressionDetector()
        with pytest.raises(RegressionDetectionError):
            await detector.create_baseline("comp1", ["nonexistent"])


class TestDetectRegression:
    @pytest.mark.asyncio
    async def test_detect_no_regression_clean(self) -> None:
        detector = RegressionDetector()
        baseline_execs = [
            TestExecution(
                id="e1", test_id="tc1", status=TestExecutionStatus.PASSED, duration_ms=100.0
            ),
        ]
        detector._baselines["b1"] = baseline_execs
        detector._baselines["comp1"] = baseline_execs

        result = await detector.detect_regression("comp1", "b1", ["e1"])
        assert result.status is RegressionStatus.CLEAN

    @pytest.mark.asyncio
    async def test_detect_regression_failed(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = [
            TestExecution(
                id="e1", test_id="tc1", status=TestExecutionStatus.PASSED, duration_ms=100.0
            ),
        ]
        detector._baselines["comp1"] = [
            TestExecution(
                id="e2", test_id="tc1", status=TestExecutionStatus.FAILED, duration_ms=200.0
            ),
        ]

        result = await detector.detect_regression("comp1", "b1", ["e2"])
        assert result.status is RegressionStatus.REGRESSION

    @pytest.mark.asyncio
    async def test_detect_improvement(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = [
            TestExecution(
                id="e1", test_id="tc1", status=TestExecutionStatus.FAILED, duration_ms=200.0
            ),
        ]
        detector._baselines["comp1"] = [
            TestExecution(
                id="e2", test_id="tc1", status=TestExecutionStatus.PASSED, duration_ms=100.0
            ),
        ]

        result = await detector.detect_regression("comp1", "b1", ["e2"])
        assert result.status is RegressionStatus.IMPROVED

    @pytest.mark.asyncio
    async def test_detect_baseline_not_found(self) -> None:
        detector = RegressionDetector()
        with pytest.raises(RegressionDetectionError):
            await detector.detect_regression("comp1", "nonexistent", [])

    @pytest.mark.asyncio
    async def test_detect_no_current_executions(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = []
        with pytest.raises(RegressionDetectionError):
            await detector.detect_regression("comp1", "b1", [])

    @pytest.mark.asyncio
    async def test_detect_changes_tracked(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = [
            TestExecution(
                id="e1", test_id="tc1", status=TestExecutionStatus.PASSED, duration_ms=100.0
            ),
        ]
        detector._baselines["comp1"] = [
            TestExecution(
                id="e2", test_id="tc1", status=TestExecutionStatus.FAILED, duration_ms=200.0
            ),
        ]

        result = await detector.detect_regression("comp1", "b1", ["e2"])
        assert len(result.changes) == 1
        change = result.changes[0]
        assert change.test_id == "tc1"
        assert change.delta_ms == 100.0


class TestGetAndListRegressions:
    @pytest.mark.asyncio
    async def test_get_regression_result(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED)
        ]
        detector._baselines["comp1"] = [
            TestExecution(id="e2", test_id="tc1", status=TestExecutionStatus.PASSED)
        ]
        result = await detector.detect_regression("comp1", "b1", ["e2"])
        fetched = await detector.get_regression_result(result.id)
        assert fetched.id == result.id

    @pytest.mark.asyncio
    async def test_get_regression_missing(self) -> None:
        detector = RegressionDetector()
        with pytest.raises(RegressionDetectionError):
            await detector.get_regression_result("nonexistent")

    @pytest.mark.asyncio
    async def test_list_regressions(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED)
        ]
        detector._baselines["comp1"] = [
            TestExecution(id="e2", test_id="tc1", status=TestExecutionStatus.PASSED)
        ]
        await detector.detect_regression("comp1", "b1", ["e2"])
        results = await detector.list_regressions()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_list_regressions_empty(self) -> None:
        detector = RegressionDetector()
        results = await detector.list_regressions()
        assert results == []

    @pytest.mark.asyncio
    async def test_list_regressions_filtered(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = [
            TestExecution(id="e1", test_id="tc1", status=TestExecutionStatus.PASSED)
        ]
        detector._baselines["comp1"] = [
            TestExecution(id="e2", test_id="tc1", status=TestExecutionStatus.PASSED)
        ]
        await detector.detect_regression("comp1", "b1", ["e2"])
        results = await detector.list_regressions(component="comp1")
        assert len(results) == 1


class TestComparePerformance:
    @pytest.mark.asyncio
    async def test_compare_performance(self) -> None:
        detector = RegressionDetector()
        detector._baselines["b1"] = [
            TestExecution(
                id="e1", test_id="tc1", status=TestExecutionStatus.PASSED, duration_ms=100.0
            ),
        ]
        detector._baselines["comp1"] = [
            TestExecution(
                id="e2", test_id="tc1", status=TestExecutionStatus.FAILED, duration_ms=200.0
            ),
        ]
        result = await detector.detect_regression("comp1", "b1", ["e2"])
        perf = await detector.compare_performance("tc1", "b1", result.id)
        assert perf["baseline_duration_ms"] == 100.0
        assert perf["delta_ms"] == 100.0

    @pytest.mark.asyncio
    async def test_compare_performance_baseline_not_found(self) -> None:
        detector = RegressionDetector()
        with pytest.raises(RegressionDetectionError):
            await detector.compare_performance("tc1", "nonexistent", "nonexistent")
