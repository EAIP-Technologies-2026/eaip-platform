"""Tests for model evaluation & benchmarking models, events, exceptions, and service."""

from __future__ import annotations

import pytest

from eaip.model_evaluation.events import (
    BenchmarkComparisonComputed,
    BenchmarkCompleted,
    BenchmarkCreated,
    BenchmarkFailed,
    BenchmarkStarted,
    EvaluationCancelled,
    EvaluationCompleted,
    EvaluationConfigUpdated,
    EvaluationCreated,
    EvaluationDatasetPrepared,
    EvaluationFailed,
    EvaluationStarted,
    EvaluationSummaryGenerated,
    MetricRecorded,
    ModelProfileUpdated,
)
from eaip.model_evaluation.exceptions import (
    BenchmarkConfigError,
    BenchmarkFailedError,
    BenchmarkNotFoundError,
    EvaluationConfigError,
    EvaluationFailedError,
    EvaluationNotFoundError,
    ModelEvaluationError,
    ModelProfileError,
)
from eaip.model_evaluation.models import (
    BenchmarkComparison,
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkScore,
    BenchmarkStatus,
    EvaluationConfig,
    EvaluationDataset,
    EvaluationMetric,
    EvaluationResult,
    EvaluationRun,
    EvaluationStatus,
    EvaluationSummary,
    MetricType,
    ModelBenchmark,
    ModelEvaluation,
    ModelPerformanceProfile,
)
from eaip.model_evaluation.service import ModelEvaluationService

# ── model tests ──────────────────────────────────────────────────────────────


class TestEvaluationStatus:
    def test_values(self) -> None:
        assert EvaluationStatus.PENDING.value == "pending"
        assert EvaluationStatus.RUNNING.value == "running"
        assert EvaluationStatus.COMPLETED.value == "completed"
        assert EvaluationStatus.FAILED.value == "failed"
        assert EvaluationStatus.CANCELLED.value == "cancelled"


class TestMetricType:
    def test_values(self) -> None:
        assert MetricType.ACCURACY.value == "accuracy"
        assert MetricType.CUSTOM.value == "custom"


class TestBenchmarkStatus:
    def test_values(self) -> None:
        assert BenchmarkStatus.PENDING.value == "pending"
        assert BenchmarkStatus.COMPLETED.value == "completed"


class TestEvaluationMetric:
    def test_create(self) -> None:
        m = EvaluationMetric(name="acc", type=MetricType.ACCURACY, value=0.95)
        assert m.name == "acc"
        assert m.type == MetricType.ACCURACY
        assert m.value == 0.95
        assert m.unit == ""
        assert not m.metadata

    def test_frozen(self) -> None:
        m = EvaluationMetric(name="prec", type=MetricType.PRECISION, value=0.89)
        with pytest.raises(ValueError, match="frozen instance"):
            m.value = 0.5


class TestEvaluationConfig:
    def test_create(self) -> None:
        cfg = EvaluationConfig(id="cfg1", name="test-eval", model_id="m1")
        assert cfg.id == "cfg1"
        assert cfg.model_id == "m1"
        assert cfg.max_samples == 0
        assert cfg.timeout_seconds == 300

    def test_frozen(self) -> None:
        cfg = EvaluationConfig(id="cfg1", name="test-eval", model_id="m1")
        with pytest.raises(ValueError, match="frozen instance"):
            cfg.name = "new"


class TestEvaluationResult:
    def test_create(self) -> None:
        r = EvaluationResult(
            id="r1", config_id="cfg1", model_id="m1", status=EvaluationStatus.PENDING
        )
        assert r.id == "r1"
        assert r.status == EvaluationStatus.PENDING

    def test_defaults(self) -> None:
        r = EvaluationResult(
            id="r1", config_id="cfg1", model_id="m1", status=EvaluationStatus.COMPLETED
        )
        assert r.metrics == ()
        assert r.error_message == ""
        assert r.duration_ms == 0.0


class TestModelEvaluation:
    def test_create(self) -> None:
        e = ModelEvaluation(
            id="e1", config_id="cfg1", model_id="m1", status=EvaluationStatus.PENDING
        )
        assert e.id == "e1"
        assert e.results == ()


class TestEvaluationDataset:
    def test_create(self) -> None:
        ds = EvaluationDataset(id="ds1", name="test-ds", record_count=100)
        assert ds.id == "ds1"
        assert ds.description == ""
        assert ds.version == ""

    def test_schema_alias(self) -> None:
        ds = EvaluationDataset(id="ds1", name="test-ds", schema={"type": "object"})
        assert ds.schema_ == {"type": "object"}


class TestEvaluationRun:
    def test_create(self) -> None:
        run = EvaluationRun(id="run1", evaluation_id="e1", status=EvaluationStatus.PENDING)
        assert run.id == "run1"
        assert run.result_ids == ()


class TestEvaluationSummary:
    def test_create(self) -> None:
        s = EvaluationSummary(id="s1")
        assert s.total_count == 0
        assert s.completed_count == 0


class TestBenchmarkConfig:
    def test_create(self) -> None:
        cfg = BenchmarkConfig(id="bc1", name="test-benchmark")
        assert cfg.id == "bc1"
        assert cfg.iterations == 1
        assert cfg.timeout_seconds == 600


class TestBenchmarkResult:
    def test_create(self) -> None:
        r = BenchmarkResult(
            id="br1", config_id="bc1", model_id="m1", status=BenchmarkStatus.PENDING
        )
        assert r.scores == ()


class TestModelBenchmark:
    def test_create(self) -> None:
        b = ModelBenchmark(id="b1", config_id="bc1", name="bench1", status=BenchmarkStatus.PENDING)
        assert b.results == ()


class TestBenchmarkScore:
    def test_create(self) -> None:
        s = BenchmarkScore(metric=MetricType.ACCURACY, value=0.92)
        assert s.weight == 1.0


class TestBenchmarkComparison:
    def test_create(self) -> None:
        c = BenchmarkComparison(id="cmp1", benchmark_id="b1")
        assert c.ranking == ()


class TestModelPerformanceProfile:
    def test_create(self) -> None:
        p = ModelPerformanceProfile(model_id="m1")
        assert p.evaluation_count == 0
        assert p.benchmark_count == 0


# ── event tests ──────────────────────────────────────────────────────────────


class TestEvaluationCreated:
    def test_event_type(self) -> None:
        ev = EvaluationCreated(evaluation_id="e1", model_id="m1", config_id="cfg1")
        assert ev.event_type == "eaip.model_evaluation.evaluation.created"
        assert ev.evaluation_id == "e1"

    def test_occurred_at_set(self) -> None:
        ev = EvaluationCreated(evaluation_id="e1", model_id="m1", config_id="cfg1")
        assert ev.occurred_at is not None


class TestEvaluationStarted:
    def test_event_type(self) -> None:
        ev = EvaluationStarted(evaluation_id="e1", model_id="m1", run_id="run1")
        assert ev.event_type == "eaip.model_evaluation.evaluation.started"


class TestEvaluationCompleted:
    def test_event_type(self) -> None:
        ev = EvaluationCompleted(evaluation_id="e1", model_id="m1", result_id="r1")
        assert ev.event_type == "eaip.model_evaluation.evaluation.completed"


class TestEvaluationFailed:
    def test_event_type(self) -> None:
        ev = EvaluationFailed(evaluation_id="e1", model_id="m1", error_message="err")
        assert ev.event_type == "eaip.model_evaluation.evaluation.failed"


class TestEvaluationCancelled:
    def test_event_type(self) -> None:
        ev = EvaluationCancelled(evaluation_id="e1", model_id="m1")
        assert ev.event_type == "eaip.model_evaluation.evaluation.cancelled"


class TestMetricRecorded:
    def test_event_type(self) -> None:
        ev = MetricRecorded(
            evaluation_id="e1", result_id="r1", metric_name="acc", metric_value=0.95
        )
        assert ev.event_type == "eaip.model_evaluation.metric.recorded"


class TestBenchmarkEvents:
    def test_created(self) -> None:
        ev = BenchmarkCreated(benchmark_id="b1", config_id="bc1")
        assert ev.event_type == "eaip.model_evaluation.benchmark.created"

    def test_started(self) -> None:
        ev = BenchmarkStarted(benchmark_id="b1")
        assert ev.event_type == "eaip.model_evaluation.benchmark.started"

    def test_completed(self) -> None:
        ev = BenchmarkCompleted(benchmark_id="b1")
        assert ev.event_type == "eaip.model_evaluation.benchmark.completed"

    def test_failed(self) -> None:
        ev = BenchmarkFailed(benchmark_id="b1", error_message="err")
        assert ev.event_type == "eaip.model_evaluation.benchmark.failed"


class TestBenchmarkComparisonComputed:
    def test_event_type(self) -> None:
        ev = BenchmarkComparisonComputed(
            comparison_id="cmp1", benchmark_id="b1", ranked_models=("m1", "m2")
        )
        assert ev.event_type == "eaip.model_evaluation.benchmark.comparison_computed"


class TestEvaluationSummaryGenerated:
    def test_event_type(self) -> None:
        ev = EvaluationSummaryGenerated(summary_id="s1", evaluation_count=3)
        assert ev.event_type == "eaip.model_evaluation.evaluation.summary_generated"


class TestModelProfileUpdated:
    def test_event_type(self) -> None:
        ev = ModelProfileUpdated(model_id="m1")
        assert ev.event_type == "eaip.model_evaluation.profile.updated"


class TestEvaluationDatasetPrepared:
    def test_event_type(self) -> None:
        ev = EvaluationDatasetPrepared(dataset_id="ds1", name="test-ds")
        assert ev.event_type == "eaip.model_evaluation.dataset.prepared"


class TestEvaluationConfigUpdated:
    def test_event_type(self) -> None:
        ev = EvaluationConfigUpdated(config_id="cfg1", model_id="m1")
        assert ev.event_type == "eaip.model_evaluation.config.updated"


# ── exception tests ──────────────────────────────────────────────────────────


class TestExceptions:
    def test_base_inheritance(self) -> None:
        assert issubclass(ModelEvaluationError, Exception)

    def test_evaluation_not_found(self) -> None:
        exc = EvaluationNotFoundError("not found")
        assert "not found" in str(exc)

    def test_evaluation_failed(self) -> None:
        exc = EvaluationFailedError("failed")
        assert "failed" in str(exc)

    def test_evaluation_config_error(self) -> None:
        exc = EvaluationConfigError("bad config")
        assert "bad config" in str(exc)

    def test_benchmark_not_found(self) -> None:
        exc = BenchmarkNotFoundError("not found")
        assert "not found" in str(exc)

    def test_benchmark_failed(self) -> None:
        exc = BenchmarkFailedError("failed")
        assert "failed" in str(exc)

    def test_benchmark_config_error(self) -> None:
        exc = BenchmarkConfigError("bad config")
        assert "bad config" in str(exc)

    def test_model_profile_error(self) -> None:
        exc = ModelProfileError("profile error")
        assert "profile error" in str(exc)


# ── service tests ────────────────────────────────────────────────────────────


@pytest.fixture
def service() -> ModelEvaluationService:
    return ModelEvaluationService()


@pytest.fixture
def eval_config() -> EvaluationConfig:
    return EvaluationConfig(id="cfg1", name="test-eval", model_id="m1")


@pytest.fixture
def evaluation() -> ModelEvaluation:
    return ModelEvaluation(
        id="e1", config_id="cfg1", model_id="m1", status=EvaluationStatus.PENDING
    )


@pytest.fixture
def benchmark_config() -> BenchmarkConfig:
    return BenchmarkConfig(id="bc1", name="test-benchmark", model_ids=("m1", "m2"))


@pytest.fixture
def benchmark() -> ModelBenchmark:
    return ModelBenchmark(id="b1", config_id="bc1", name="bench1", status=BenchmarkStatus.PENDING)


class TestModelEvaluationServiceConfigs:
    async def test_create_and_get_config(
        self, service: ModelEvaluationService, eval_config: EvaluationConfig
    ) -> None:
        created = await service.create_evaluation_config(eval_config)
        assert created.id == "cfg1"
        fetched = await service.get_evaluation_config("cfg1")
        assert fetched.name == "test-eval"

    async def test_get_config_not_found(self, service: ModelEvaluationService) -> None:
        with pytest.raises(EvaluationConfigError):
            await service.get_evaluation_config("nonexistent")

    async def test_update_config(
        self, service: ModelEvaluationService, eval_config: EvaluationConfig
    ) -> None:
        await service.create_evaluation_config(eval_config)
        updated = await service.update_evaluation_config("cfg1", name="updated-eval")
        assert updated.name == "updated-eval"

    async def test_delete_config(
        self, service: ModelEvaluationService, eval_config: EvaluationConfig
    ) -> None:
        await service.create_evaluation_config(eval_config)
        await service.delete_evaluation_config("cfg1")
        with pytest.raises(EvaluationConfigError):
            await service.get_evaluation_config("cfg1")

    async def test_list_configs(
        self, service: ModelEvaluationService, eval_config: EvaluationConfig
    ) -> None:
        assert await service.list_evaluation_configs() == []
        await service.create_evaluation_config(eval_config)
        assert len(await service.list_evaluation_configs()) == 1


class TestModelEvaluationServiceEvaluations:
    async def test_create_and_get(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        created = await service.create_evaluation(evaluation)
        assert created.id == "e1"
        fetched = await service.get_evaluation("e1")
        assert fetched.status == EvaluationStatus.PENDING

    async def test_get_not_found(self, service: ModelEvaluationService) -> None:
        with pytest.raises(EvaluationNotFoundError):
            await service.get_evaluation("nonexistent")

    async def test_start_evaluation(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        updated, run = await service.start_evaluation("e1")
        assert updated.status == EvaluationStatus.RUNNING
        assert run.status == EvaluationStatus.RUNNING
        assert run.evaluation_id == "e1"

    async def test_start_non_pending_fails(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        ev = evaluation.model_copy(update={"status": EvaluationStatus.COMPLETED})
        await service.create_evaluation(ev)
        with pytest.raises(EvaluationFailedError):
            await service.start_evaluation("e1")

    async def test_complete_evaluation(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        result = EvaluationResult(
            id="r1", config_id="cfg1", model_id="m1", status=EvaluationStatus.COMPLETED
        )
        updated, _ = await service.complete_evaluation("e1", result)
        assert updated.status == EvaluationStatus.COMPLETED
        assert len(updated.results) == 1

    async def test_fail_evaluation(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        updated = await service.fail_evaluation("e1", "something went wrong")
        assert updated.status == EvaluationStatus.FAILED

    async def test_cancel_evaluation(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        updated = await service.cancel_evaluation("e1")
        assert updated.status == EvaluationStatus.CANCELLED

    async def test_cancel_completed_fails(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        ev = evaluation.model_copy(update={"status": EvaluationStatus.COMPLETED})
        await service.create_evaluation(ev)
        with pytest.raises(EvaluationFailedError):
            await service.cancel_evaluation("e1")

    async def test_list_evaluations(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        assert len(await service.list_evaluations()) == 1

    async def test_delete_evaluation(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        await service.delete_evaluation("e1")
        with pytest.raises(EvaluationNotFoundError):
            await service.get_evaluation("e1")


class TestModelEvaluationServiceRuns:
    async def test_get_run_not_found(self, service: ModelEvaluationService) -> None:
        with pytest.raises(EvaluationNotFoundError):
            await service.get_evaluation_run("nonexistent")

    async def test_complete_run(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        _, run = await service.start_evaluation("e1")
        completed = await service.complete_evaluation_run(run.id)
        assert completed.status == EvaluationStatus.COMPLETED


class TestModelEvaluationServiceSummary:
    async def test_generate_summary(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        summary = await service.generate_summary(["e1"])
        assert summary.total_count == 1
        assert summary.completed_count == 0

    async def test_get_summary_not_found(self, service: ModelEvaluationService) -> None:
        with pytest.raises(EvaluationNotFoundError):
            await service.get_summary("nonexistent")


class TestModelEvaluationServiceBenchmarks:
    async def test_create_and_get_benchmark_config(
        self, service: ModelEvaluationService, benchmark_config: BenchmarkConfig
    ) -> None:
        created = await service.create_benchmark_config(benchmark_config)
        assert created.id == "bc1"
        fetched = await service.get_benchmark_config("bc1")
        assert fetched.name == "test-benchmark"

    async def test_create_and_get_benchmark(
        self, service: ModelEvaluationService, benchmark: ModelBenchmark
    ) -> None:
        created = await service.create_benchmark(benchmark)
        assert created.id == "b1"
        fetched = await service.get_benchmark("b1")
        assert fetched.status == BenchmarkStatus.PENDING

    async def test_start_benchmark(
        self,
        service: ModelEvaluationService,
        benchmark: ModelBenchmark,
        benchmark_config: BenchmarkConfig,
    ) -> None:
        await service.create_benchmark_config(benchmark_config)
        await service.create_benchmark(benchmark)
        updated, result = await service.start_benchmark("b1")
        assert updated.status == BenchmarkStatus.RUNNING
        assert result.status == BenchmarkStatus.RUNNING

    async def test_complete_benchmark(
        self,
        service: ModelEvaluationService,
        benchmark: ModelBenchmark,
        benchmark_config: BenchmarkConfig,
    ) -> None:
        await service.create_benchmark_config(benchmark_config)
        await service.create_benchmark(benchmark)
        await service.start_benchmark("b1")
        results = await service.list_benchmark_results("b1")
        await service.complete_benchmark("b1", results[0].id)
        b = await service.get_benchmark("b1")
        assert b.status == BenchmarkStatus.COMPLETED

    async def test_fail_benchmark(
        self,
        service: ModelEvaluationService,
        benchmark: ModelBenchmark,
        benchmark_config: BenchmarkConfig,
    ) -> None:
        await service.create_benchmark_config(benchmark_config)
        await service.create_benchmark(benchmark)
        await service.fail_benchmark("b1", "error")
        b = await service.get_benchmark("b1")
        assert b.status == BenchmarkStatus.FAILED

    async def test_cancel_benchmark(
        self,
        service: ModelEvaluationService,
        benchmark: ModelBenchmark,
        benchmark_config: BenchmarkConfig,
    ) -> None:
        await service.create_benchmark_config(benchmark_config)
        await service.create_benchmark(benchmark)
        await service.cancel_benchmark("b1")
        b = await service.get_benchmark("b1")
        assert b.status == BenchmarkStatus.CANCELLED

    async def test_compute_comparison(
        self,
        service: ModelEvaluationService,
        benchmark: ModelBenchmark,
        benchmark_config: BenchmarkConfig,
    ) -> None:
        await service.create_benchmark_config(benchmark_config)
        await service.create_benchmark(benchmark)
        result = BenchmarkResult(
            id="br1",
            config_id="bc1",
            model_id="m1",
            status=BenchmarkStatus.COMPLETED,
            scores=(
                BenchmarkScore(metric=MetricType.ACCURACY, value=0.95),
                BenchmarkScore(metric=MetricType.LATENCY, value=120.0, weight=0.5),
            ),
        )
        updated_benchmark = benchmark.model_copy(
            update={
                "status": BenchmarkStatus.COMPLETED,
                "results": (result,),
            }
        )
        await service.create_benchmark(updated_benchmark)
        comparison = await service.compute_comparison("b1")
        assert comparison.benchmark_id == "b1"
        assert "m1" in comparison.ranking


class TestModelEvaluationServiceProfiles:
    async def test_get_or_create(self, service: ModelEvaluationService) -> None:
        profile = await service.get_or_create_profile("m1")
        assert profile.model_id == "m1"
        assert profile.evaluation_count == 0

    async def test_update_profile(
        self, service: ModelEvaluationService, evaluation: ModelEvaluation
    ) -> None:
        await service.create_evaluation(evaluation)
        result = EvaluationResult(
            id="r1",
            config_id="cfg1",
            model_id="m1",
            status=EvaluationStatus.COMPLETED,
            metrics=(EvaluationMetric(name="accuracy", type=MetricType.ACCURACY, value=0.95),),
        )
        await service.complete_evaluation("e1", result)
        profile = await service.update_profile("m1", evaluation_ids=["e1"])
        assert profile.evaluation_count == 1
        assert profile.avg_metrics.get("accuracy", 0.0) == pytest.approx(0.95)

    async def test_get_profile_not_found(self, service: ModelEvaluationService) -> None:
        with pytest.raises(ModelProfileError):
            await service.get_profile("nonexistent")

    async def test_list_profiles(self, service: ModelEvaluationService) -> None:
        await service.get_or_create_profile("m1")
        assert len(await service.list_profiles()) == 1
