"""Regression detector — compare test executions against baselines."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.quality.exceptions import RegressionDetectionError
from eaip.quality.models import (
    RegressionChange,
    RegressionResult,
    RegressionStatus,
    TestExecution,
    TestExecutionStatus,
)
from eaip.shared.time import utc_now


class RegressionDetector:
    def __init__(self) -> None:
        self._baselines: dict[str, list[TestExecution]] = {}
        self._regression_results: dict[str, RegressionResult] = {}

    async def create_baseline(
        self,
        component: str,
        execution_ids: list[str],
        baselines: dict[str, list[TestExecution]] | None = None,
    ) -> dict[str, Any]:
        executions = (baselines or self._baselines).get(component, [])
        requested = [e for e in executions if e.id in execution_ids]
        if not requested:
            raise RegressionDetectionError(f"No executions found for component {component!r}")

        baseline_id = str(uuid.uuid4())
        self._baselines[baseline_id] = requested
        return {
            "baseline_id": baseline_id,
            "component": component,
            "execution_count": len(requested),
        }

    async def detect_regression(
        self,
        component: str,
        baseline_id: str,
        execution_ids: list[str],
    ) -> RegressionResult:
        if baseline_id not in self._baselines:
            raise RegressionDetectionError(f"Baseline {baseline_id!r} not found")

        baseline_execs = self._baselines[baseline_id]
        current_execs = [e for e in self._baselines.get(component, []) if e.id in execution_ids]
        if not current_execs:
            raise RegressionDetectionError(
                f"No current executions found for component {component!r}"
            )

        baseline_map: dict[str, TestExecution] = {}
        for be in baseline_execs:
            baseline_map[be.test_id] = be

        current_map: dict[str, TestExecution] = {}
        for ce in current_execs:
            current_map[ce.test_id] = ce

        all_test_ids = set(baseline_map.keys()) | set(current_map.keys())
        changes: list[RegressionChange] = []
        has_regression = False
        has_improvement = False

        for test_id in sorted(all_test_ids):
            baseline = baseline_map.get(test_id)
            current = current_map.get(test_id)

            baseline_status = baseline.status.value if baseline else "unknown"
            current_status = current.status.value if current else "unknown"
            baseline_duration = baseline.duration_ms if baseline else 0.0
            current_duration = current.duration_ms if current else 0.0
            delta = current_duration - baseline_duration
            test_name = test_id

            change = RegressionChange(
                test_id=test_id,
                test_name=test_name,
                baseline_status=baseline_status,
                current_status=current_status,
                baseline_duration_ms=baseline_duration,
                current_duration_ms=current_duration,
                delta_ms=delta,
            )
            changes.append(change)

            if current and baseline:
                if (
                    current.status is TestExecutionStatus.FAILED
                    and baseline.status is TestExecutionStatus.PASSED
                ) or (
                    current.status is TestExecutionStatus.ERROR
                    and baseline.status is TestExecutionStatus.PASSED
                ):
                    has_regression = True
                elif (
                    current.status is TestExecutionStatus.PASSED
                    and baseline.status is TestExecutionStatus.FAILED
                ) or (
                    current.status is TestExecutionStatus.PASSED
                    and baseline.status is TestExecutionStatus.ERROR
                ):
                    has_improvement = True

        if has_regression:
            status = RegressionStatus.REGRESSION
        elif has_improvement:
            status = RegressionStatus.IMPROVED
        else:
            status = RegressionStatus.CLEAN

        regression_id = str(uuid.uuid4())
        result = RegressionResult(
            id=regression_id,
            baseline_id=baseline_id,
            current_id=component,
            component=component,
            status=status,
            changes=tuple(changes),
            generated_at=utc_now(),
        )
        self._regression_results[regression_id] = result
        return result

    async def get_regression_result(self, regression_id: str) -> RegressionResult:
        if regression_id not in self._regression_results:
            raise RegressionDetectionError(f"Regression result {regression_id!r} not found")
        return self._regression_results[regression_id]

    async def list_regressions(
        self,
        component: str | None = None,
        status: str | None = None,
    ) -> list[RegressionResult]:
        results: list[RegressionResult] = list(self._regression_results.values())
        if component is not None:
            results = [r for r in results if r.component == component]
        if status is not None:
            results = [r for r in results if r.status == status]
        return results

    async def compare_performance(
        self,
        test_id: str,
        baseline_id: str,
        current_id: str,
    ) -> dict[str, Any]:
        if baseline_id not in self._baselines:
            raise RegressionDetectionError(f"Baseline {baseline_id!r} not found")
        if current_id not in self._regression_results:
            raise RegressionDetectionError(f"Regression result {current_id!r} not found")

        baseline_execs = self._baselines[baseline_id]
        baseline = next((e for e in baseline_execs if e.test_id == test_id), None)
        result = self._regression_results[current_id]
        current_change = next((c for c in result.changes if c.test_id == test_id), None)

        if baseline is None and current_change is None:
            raise RegressionDetectionError(f"No performance data for test {test_id!r}")

        return {
            "test_id": test_id,
            "baseline_duration_ms": baseline.duration_ms if baseline else 0.0,
            "current_duration_ms": current_change.current_duration_ms if current_change else 0.0,
            "delta_ms": current_change.delta_ms if current_change else 0.0,
        }
