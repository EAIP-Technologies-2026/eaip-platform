"""Benchmark engine — defines and executes performance benchmarks."""

from __future__ import annotations

import math
import uuid
from typing import Any

from eaip.perf.events import BenchmarkCreated, BenchmarkRunCompleted, BenchmarkRunFailed
from eaip.perf.exceptions import BenchmarkNotFoundError, BenchmarkRunError
from eaip.perf.models import BenchmarkDefinition, BenchmarkRun, BenchmarkRunStatus, MetricType
from eaip.shared.time import utc_now


class BenchmarkEngine:
    def __init__(self) -> None:
        self._benchmarks: dict[str, BenchmarkDefinition] = {}
        self._runs: dict[str, BenchmarkRun] = {}
        self._event_callback: Any = None

    def set_event_callback(self, callback: Any) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback is not None:
            self._event_callback(event)

    def create_benchmark(self, benchmark: BenchmarkDefinition) -> BenchmarkDefinition:
        self._benchmarks[benchmark.id] = benchmark
        self._emit(
            BenchmarkCreated(
                benchmark_id=benchmark.id,
                name=benchmark.name,
                component=benchmark.component,
                metric_type=benchmark.metric_type.value,
            )
        )
        return benchmark

    def get_benchmark(self, benchmark_id: str) -> BenchmarkDefinition:
        if benchmark_id not in self._benchmarks:
            raise BenchmarkNotFoundError(f"Benchmark {benchmark_id!r} not found")
        return self._benchmarks[benchmark_id]

    def update_benchmark(self, benchmark_id: str, **updates: Any) -> BenchmarkDefinition:
        existing = self.get_benchmark(benchmark_id)
        updated = existing.model_copy(update=updates)
        self._benchmarks[benchmark_id] = updated
        return updated

    def delete_benchmark(self, benchmark_id: str) -> None:
        if benchmark_id not in self._benchmarks:
            raise BenchmarkNotFoundError(f"Benchmark {benchmark_id!r} not found")
        del self._benchmarks[benchmark_id]

    def list_benchmarks(
        self,
        component: str | None = None,
        metric_type: str | None = None,
        enabled: bool | None = None,
    ) -> list[BenchmarkDefinition]:
        results: list[BenchmarkDefinition] = list(self._benchmarks.values())
        if component is not None:
            results = [b for b in results if b.component == component]
        if metric_type is not None:
            results = [b for b in results if b.metric_type == metric_type]
        if enabled is not None:
            results = [b for b in results if b.enabled is enabled]
        return results

    async def run_benchmark(
        self,
        benchmark_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkRun:
        benchmark = self.get_benchmark(benchmark_id)
        if not benchmark.enabled:
            run_id = str(uuid.uuid4())
            run = BenchmarkRun(
                id=run_id,
                benchmark_id=benchmark_id,
                status=BenchmarkRunStatus.FAILED,
                completed_at=utc_now(),
                error="Benchmark is disabled",
                metadata=metadata or {},
            )
            self._runs[run_id] = run
            self._emit(
                BenchmarkRunFailed(
                    run_id=run_id,
                    benchmark_id=benchmark_id,
                    error="Benchmark is disabled",
                ),
            )
            return run

        run_id = str(uuid.uuid4())
        run = BenchmarkRun(
            id=run_id,
            benchmark_id=benchmark_id,
            status=BenchmarkRunStatus.RUNNING,
            started_at=utc_now(),
            metadata=metadata or {},
        )
        self._runs[run_id] = run

        try:
            result_value = self._compute_benchmark(benchmark)
            completed = utc_now()
            if run.started_at:
                duration = (completed - run.started_at).total_seconds() * 1000.0
            else:
                duration = 0.0
            if benchmark.threshold_value > 0:
                passed = result_value <= benchmark.threshold_value
            else:
                passed = True

            run = BenchmarkRun(
                id=run_id,
                benchmark_id=benchmark_id,
                status=BenchmarkRunStatus.COMPLETED,
                started_at=run.started_at,
                completed_at=completed,
                duration_ms=duration,
                result_value=result_value,
                passed=passed,
                metadata=metadata or {},
            )
            self._emit(
                BenchmarkRunCompleted(
                    run_id=run_id,
                    benchmark_id=benchmark_id,
                    result_value=result_value,
                    passed=passed,
                    duration_ms=duration,
                )
            )
        except Exception as exc:
            completed = utc_now()
            if run.started_at:
                duration = (completed - run.started_at).total_seconds() * 1000.0
            else:
                duration = 0.0
            run = BenchmarkRun(
                id=run_id,
                benchmark_id=benchmark_id,
                status=BenchmarkRunStatus.FAILED,
                started_at=run.started_at,
                completed_at=completed,
                duration_ms=duration,
                error=str(exc),
                metadata=metadata or {},
            )
            self._emit(BenchmarkRunFailed(run_id=run_id, benchmark_id=benchmark_id, error=str(exc)))

        self._runs[run_id] = run
        return run

    async def run_all(
        self,
        metadata: dict[str, Any] | None = None,
    ) -> list[BenchmarkRun]:
        benchmarks = self.list_benchmarks(enabled=True)
        runs: list[BenchmarkRun] = []
        for benchmark in benchmarks:
            run = await self.run_benchmark(benchmark.id, metadata)
            runs.append(run)
        return runs

    async def get_run_history(
        self,
        benchmark_id: str,
        limit: int = 100,
    ) -> list[BenchmarkRun]:
        self.get_benchmark(benchmark_id)
        results: list[BenchmarkRun] = [
            r for r in self._runs.values() if r.benchmark_id == benchmark_id
        ]
        results.sort(key=lambda r: r.started_at or utc_now(), reverse=True)
        return results[:limit]

    async def compare_runs(
        self,
        benchmark_id: str,
        run_a_id: str,
        run_b_id: str,
    ) -> dict[str, Any]:
        self.get_benchmark(benchmark_id)
        run_a = self._runs.get(run_a_id)
        run_b = self._runs.get(run_b_id)
        if run_a is None:
            raise BenchmarkRunError(f"Run {run_a_id!r} not found")
        if run_b is None:
            raise BenchmarkRunError(f"Run {run_b_id!r} not found")
        if run_a.benchmark_id != benchmark_id:
            msg = f"Run {run_a_id!r} does not belong to benchmark {benchmark_id!r}"
            raise BenchmarkRunError(msg)
        if run_b.benchmark_id != benchmark_id:
            msg = f"Run {run_b_id!r} does not belong to benchmark {benchmark_id!r}"
            raise BenchmarkRunError(msg)

        delta = run_b.result_value - run_a.result_value
        pct_change = (delta / run_a.result_value * 100.0) if run_a.result_value != 0 else 0.0

        return {
            "benchmark_id": benchmark_id,
            "run_a_id": run_a_id,
            "run_b_id": run_b_id,
            "run_a_value": run_a.result_value,
            "run_b_value": run_b.result_value,
            "delta": delta,
            "change_percent": round(pct_change, 2),
            "run_a_passed": run_a.passed,
            "run_b_passed": run_b.passed,
        }

    async def get_run(self, run_id: str) -> BenchmarkRun:
        if run_id not in self._runs:
            raise BenchmarkRunError(f"Run {run_id!r} not found")
        return self._runs[run_id]

    @staticmethod
    def _compute_benchmark(benchmark: BenchmarkDefinition) -> float:
        if benchmark.metric_type is MetricType.LATENCY:
            return round(abs(math.sin(hash(benchmark.id))) * 100, 2)
        if benchmark.metric_type is MetricType.THROUGHPUT:
            return round(abs(math.cos(hash(benchmark.id))) * 1000, 2)
        if benchmark.metric_type is MetricType.MEMORY:
            return round(abs(math.tan(hash(benchmark.id) % 100)) * 50, 2)
        if benchmark.metric_type is MetricType.CPU:
            return round(abs(math.log1p(abs(hash(benchmark.id) % 100))) * 10, 2)
        return round(abs(hash(benchmark.id)) % 1000 / 10.0, 2)
