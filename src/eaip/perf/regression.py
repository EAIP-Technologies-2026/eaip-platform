"""Regression detector — detects performance regressions from benchmark runs."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from eaip.perf.events import FalsePositiveMarked, RegressionDetected, RegressionResolved
from eaip.perf.exceptions import RegressionNotFoundError
from eaip.perf.models import (
    BenchmarkRun,
    MetricType,
    PerformanceRegression,
    RegressionDirection,
    RegressionSeverity,
    RegressionStatus,
)
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.perf.benchmarks import BenchmarkEngine

_CRITICAL_PCT = 50.0
_HIGH_PCT = 25.0
_MEDIUM_PCT = 10.0


class RegressionDetector:
    def __init__(self, engine: BenchmarkEngine | None = None) -> None:
        self._baselines: dict[str, BenchmarkRun] = {}
        self._regressions: dict[str, PerformanceRegression] = {}
        self._event_callback: Any = None
        self._engine = engine

    def set_event_callback(self, callback: Any) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback is not None:
            self._event_callback(event)

    async def get_baseline(self, benchmark_id: str) -> BenchmarkRun | None:
        return self._baselines.get(benchmark_id)

    async def set_baseline(self, benchmark_id: str, run: BenchmarkRun) -> None:
        self._baselines[benchmark_id] = run

    async def detect_regression(
        self,
        benchmark_id: str,
        current_run_id: str,
        threshold_percent: float = 10.0,
    ) -> PerformanceRegression | None:
        baseline_run = self._baselines.get(benchmark_id)
        if baseline_run is None or self._engine is None:
            return None

        try:
            current_run = await self._engine.get_run(current_run_id)
        except Exception:
            return None

        if current_run.benchmark_id != benchmark_id:
            return None

        return await self._compare_runs(
            benchmark_id,
            baseline_run,
            current_run,
            threshold_percent,
        )

    async def detect_regression_with_runs(
        self,
        benchmark_id: str,
        baseline_run: BenchmarkRun,
        current_run: BenchmarkRun,
        threshold_percent: float = 10.0,
        metric_type: MetricType = MetricType.LATENCY,
    ) -> PerformanceRegression | None:
        if baseline_run.id == current_run.id:
            return None
        return await self._compare_runs(
            benchmark_id,
            baseline_run,
            current_run,
            threshold_percent,
            metric_type,
        )

    async def _compare_runs(
        self,
        benchmark_id: str,
        baseline_run: BenchmarkRun,
        current_run: BenchmarkRun,
        threshold_percent: float = 10.0,
        metric_type: MetricType = MetricType.LATENCY,
    ) -> PerformanceRegression:
        delta = current_run.result_value - baseline_run.result_value
        baseline_val = baseline_run.result_value
        change_percent = (delta / baseline_val * 100.0) if baseline_val != 0 else 0.0

        if abs(change_percent) < threshold_percent:
            direction = RegressionDirection.UNCHANGED
            severity = RegressionSeverity.LOW
        elif change_percent > 0:
            direction = RegressionDirection.REGRESSION
            severity = self._compute_severity(abs(change_percent))
        else:
            direction = RegressionDirection.IMPROVEMENT
            severity = RegressionSeverity.LOW

        regression_id = str(uuid.uuid4())
        regression = PerformanceRegression(
            id=regression_id,
            benchmark_id=benchmark_id,
            baseline_run_id=baseline_run.id,
            current_run_id=current_run.id,
            metric_type=metric_type,
            baseline_value=baseline_run.result_value,
            current_value=current_run.result_value,
            change_percent=round(change_percent, 2),
            direction=direction,
            severity=severity,
            detected_at=utc_now(),
            status=RegressionStatus.OPEN,
        )

        self._regressions[regression_id] = regression
        self._emit(
            RegressionDetected(
                regression_id=regression_id,
                benchmark_id=benchmark_id,
                direction=direction.value,
                severity=severity.value,
                change_percent=round(change_percent, 2),
            )
        )
        return regression

    async def acknowledge_regression(self, regression_id: str) -> PerformanceRegression:
        regression = self._get_regression(regression_id)
        updated = regression.model_copy(update={"status": RegressionStatus.ACKNOWLEDGED})
        self._regressions[regression_id] = updated
        return updated

    async def resolve_regression(self, regression_id: str) -> PerformanceRegression:
        regression = self._get_regression(regression_id)
        updated = regression.model_copy(update={"status": RegressionStatus.RESOLVED})
        self._regressions[regression_id] = updated
        self._emit(
            RegressionResolved(
                regression_id=regression_id,
                benchmark_id=regression.benchmark_id,
            )
        )
        return updated

    async def mark_false_positive(self, regression_id: str) -> PerformanceRegression:
        regression = self._get_regression(regression_id)
        updated = regression.model_copy(update={"status": RegressionStatus.FALSE_POSITIVE})
        self._regressions[regression_id] = updated
        self._emit(
            FalsePositiveMarked(
                regression_id=regression_id,
                benchmark_id=regression.benchmark_id,
            )
        )
        return updated

    async def list_regressions(
        self,
        status: str | None = None,
        benchmark_id: str | None = None,
    ) -> list[PerformanceRegression]:
        results: list[PerformanceRegression] = list(self._regressions.values())
        if status is not None:
            results = [r for r in results if r.status.value == status]
        if benchmark_id is not None:
            results = [r for r in results if r.benchmark_id == benchmark_id]
        return results

    def _get_regression(self, regression_id: str) -> PerformanceRegression:
        if regression_id not in self._regressions:
            raise RegressionNotFoundError(f"Regression {regression_id!r} not found")
        return self._regressions[regression_id]

    @staticmethod
    def _compute_severity(change_pct: float) -> RegressionSeverity:
        if change_pct >= _CRITICAL_PCT:
            return RegressionSeverity.CRITICAL
        if change_pct >= _HIGH_PCT:
            return RegressionSeverity.HIGH
        if change_pct >= _MEDIUM_PCT:
            return RegressionSeverity.MEDIUM
        return RegressionSeverity.LOW
