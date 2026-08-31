"""Tests for :mod:`eaip.perf.benchmarks`."""

from __future__ import annotations

import pytest

from eaip.perf.benchmarks import BenchmarkEngine
from eaip.perf.exceptions import BenchmarkNotFoundError, BenchmarkRunError
from eaip.perf.models import BenchmarkDefinition, BenchmarkRunStatus, MetricType

BenchmarkEngine.__test__ = False
BenchmarkDefinition.__test__ = False
BenchmarkRunStatus.__test__ = False
BenchmarkNotFoundError.__test__ = False
BenchmarkRunError.__test__ = False


class TestCreateBenchmark:
    def test_create_and_get(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1", name="p50", component="api", metric_type=MetricType.LATENCY, target_value=200.0
        )
        engine.create_benchmark(b)
        assert engine.get_benchmark("b1") is b

    def test_get_missing(self) -> None:
        engine = BenchmarkEngine()
        with pytest.raises(BenchmarkNotFoundError):
            engine.get_benchmark("nonexistent")

    def test_delete_existing(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1", name="p50", component="api", metric_type=MetricType.LATENCY, target_value=200.0
        )
        engine.create_benchmark(b)
        engine.delete_benchmark("b1")
        with pytest.raises(BenchmarkNotFoundError):
            engine.get_benchmark("b1")

    def test_delete_missing(self) -> None:
        engine = BenchmarkEngine()
        with pytest.raises(BenchmarkNotFoundError):
            engine.delete_benchmark("nonexistent")

    def test_update_benchmark(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1", name="p50", component="api", metric_type=MetricType.LATENCY, target_value=200.0
        )
        engine.create_benchmark(b)
        updated = engine.update_benchmark("b1", name="p95", target_value=500.0)
        assert updated.name == "p95"
        assert updated.target_value == 500.0

    def test_update_missing(self) -> None:
        engine = BenchmarkEngine()
        with pytest.raises(BenchmarkNotFoundError):
            engine.update_benchmark("nonexistent", name="new")


class TestListBenchmarks:
    def test_empty(self) -> None:
        engine = BenchmarkEngine()
        assert engine.list_benchmarks() == []

    def test_all(self) -> None:
        engine = BenchmarkEngine()
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b1",
                name="a",
                component="api",
                metric_type=MetricType.LATENCY,
                target_value=100.0,
            )
        )
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b2",
                name="b",
                component="db",
                metric_type=MetricType.THROUGHPUT,
                target_value=500.0,
            )
        )
        assert len(engine.list_benchmarks()) == 2

    def test_filter_by_component(self) -> None:
        engine = BenchmarkEngine()
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b1",
                name="a",
                component="api",
                metric_type=MetricType.LATENCY,
                target_value=100.0,
            )
        )
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b2",
                name="b",
                component="db",
                metric_type=MetricType.THROUGHPUT,
                target_value=500.0,
            )
        )
        result = engine.list_benchmarks(component="api")
        assert len(result) == 1
        assert result[0].id == "b1"

    def test_filter_by_metric_type(self) -> None:
        engine = BenchmarkEngine()
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b1",
                name="a",
                component="api",
                metric_type=MetricType.LATENCY,
                target_value=100.0,
            )
        )
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b2",
                name="b",
                component="api",
                metric_type=MetricType.THROUGHPUT,
                target_value=500.0,
            )
        )
        result = engine.list_benchmarks(metric_type="throughput")
        assert len(result) == 1

    def test_filter_by_enabled(self) -> None:
        engine = BenchmarkEngine()
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b1",
                name="a",
                component="api",
                metric_type=MetricType.LATENCY,
                target_value=100.0,
                enabled=True,
            )
        )
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b2",
                name="b",
                component="api",
                metric_type=MetricType.THROUGHPUT,
                target_value=500.0,
                enabled=False,
            )
        )
        result = engine.list_benchmarks(enabled=True)
        assert len(result) == 1


class TestRunBenchmark:
    @pytest.mark.asyncio
    async def test_run_disabled_benchmark(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
            enabled=False,
        )
        engine.create_benchmark(b)
        run = await engine.run_benchmark("b1")
        assert run.status is BenchmarkRunStatus.FAILED
        assert "disabled" in run.error

    @pytest.mark.asyncio
    async def test_run_missing_benchmark(self) -> None:
        engine = BenchmarkEngine()
        with pytest.raises(BenchmarkNotFoundError):
            await engine.run_benchmark("nonexistent")

    @pytest.mark.asyncio
    async def test_run_successful(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        run = await engine.run_benchmark("b1")
        assert run.status is BenchmarkRunStatus.COMPLETED
        assert run.result_value > 0
        assert run.duration_ms >= 0
        assert run.started_at is not None
        assert run.completed_at is not None

    @pytest.mark.asyncio
    async def test_run_with_metadata(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        run = await engine.run_benchmark("b1", metadata={"trigger": "scheduled"})
        assert run.metadata.get("trigger") == "scheduled"

    @pytest.mark.asyncio
    async def test_run_all(self) -> None:
        engine = BenchmarkEngine()
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b1",
                name="a",
                component="api",
                metric_type=MetricType.LATENCY,
                target_value=100.0,
            )
        )
        engine.create_benchmark(
            BenchmarkDefinition(
                id="b2",
                name="b",
                component="api",
                metric_type=MetricType.THROUGHPUT,
                target_value=500.0,
            )
        )
        runs = await engine.run_all()
        assert len(runs) == 2
        assert all(r.status is BenchmarkRunStatus.COMPLETED for r in runs)


class TestRunHistory:
    @pytest.mark.asyncio
    async def test_get_run_history_empty(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        history = await engine.get_run_history("b1")
        assert history == []

    @pytest.mark.asyncio
    async def test_get_run_history(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        await engine.run_benchmark("b1")
        await engine.run_benchmark("b1")
        history = await engine.get_run_history("b1")
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_run_history_limit(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        for _ in range(5):
            await engine.run_benchmark("b1")
        history = await engine.get_run_history("b1", limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_run_history_missing_benchmark(self) -> None:
        engine = BenchmarkEngine()
        with pytest.raises(BenchmarkNotFoundError):
            await engine.get_run_history("nonexistent")

    @pytest.mark.asyncio
    async def test_get_run(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        run = await engine.run_benchmark("b1")
        fetched = await engine.get_run(run.id)
        assert fetched.id == run.id

    @pytest.mark.asyncio
    async def test_get_run_missing(self) -> None:
        engine = BenchmarkEngine()
        with pytest.raises(BenchmarkRunError):
            await engine.get_run("nonexistent")


class TestCompareRuns:
    @pytest.mark.asyncio
    async def test_compare_runs(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        run_a = await engine.run_benchmark("b1")
        run_b = await engine.run_benchmark("b1")
        comparison = await engine.compare_runs("b1", run_a.id, run_b.id)
        assert comparison["benchmark_id"] == "b1"
        assert comparison["run_a_id"] == run_a.id
        assert comparison["run_b_id"] == run_b.id
        assert "change_percent" in comparison
        assert "delta" in comparison

    @pytest.mark.asyncio
    async def test_compare_runs_wrong_benchmark(self) -> None:
        engine = BenchmarkEngine()
        b1 = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        b2 = BenchmarkDefinition(
            id="b2",
            name="test2",
            component="api",
            metric_type=MetricType.THROUGHPUT,
            target_value=500.0,
        )
        engine.create_benchmark(b1)
        engine.create_benchmark(b2)
        run_a = await engine.run_benchmark("b1")
        run_b = await engine.run_benchmark("b2")
        with pytest.raises(BenchmarkRunError):
            await engine.compare_runs("b1", run_a.id, run_b.id)

    @pytest.mark.asyncio
    async def test_compare_runs_missing(self) -> None:
        engine = BenchmarkEngine()
        b = BenchmarkDefinition(
            id="b1",
            name="test",
            component="api",
            metric_type=MetricType.LATENCY,
            target_value=100.0,
        )
        engine.create_benchmark(b)
        with pytest.raises(BenchmarkRunError):
            await engine.compare_runs("b1", "nonexistent", "nonexistent2")
