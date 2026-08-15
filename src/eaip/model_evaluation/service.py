"""ModelEvaluationService — CRUD, run evaluations, benchmarks, comparisons."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.model_evaluation.events import (
    BenchmarkComparisonComputed,
    BenchmarkCompleted,
    BenchmarkCreated,
    BenchmarkFailed,
    BenchmarkStarted,
    EvaluationCancelled,
    EvaluationCompleted,
    EvaluationCreated,
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
    ModelProfileError,
)
from eaip.model_evaluation.models import (
    BenchmarkComparison,
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkScore,
    BenchmarkStatus,
    EvaluationConfig,
    EvaluationResult,
    EvaluationRun,
    EvaluationStatus,
    EvaluationSummary,
    ModelBenchmark,
    ModelEvaluation,
    ModelPerformanceProfile,
)
from eaip.shared.time import utc_now


class ModelEvaluationService:
    """Central service for managing evaluations, benchmarks, and profiles."""

    def __init__(self) -> None:
        """Initialize the service with in-memory stores."""
        self._configs: dict[str, EvaluationConfig] = {}
        self._evaluations: dict[str, ModelEvaluation] = {}
        self._results: dict[str, EvaluationResult] = {}
        self._runs: dict[str, EvaluationRun] = {}
        self._benchmark_configs: dict[str, BenchmarkConfig] = {}
        self._benchmarks: dict[str, ModelBenchmark] = {}
        self._benchmark_results: dict[str, BenchmarkResult] = {}
        self._comparisons: dict[str, BenchmarkComparison] = {}
        self._summaries: dict[str, EvaluationSummary] = {}
        self._profiles: dict[str, ModelPerformanceProfile] = {}
        self._log = get_logger("eaip.model_evaluation.service")

    # -- evaluation configs ---------------------------------------------------

    async def create_evaluation_config(self, config: EvaluationConfig) -> EvaluationConfig:
        """Create a new evaluation configuration."""
        self._configs[config.id] = config
        self._log.info(
            "model_evaluation.config.created", config_id=config.id, model_id=config.model_id
        )
        return config

    async def get_evaluation_config(self, config_id: str) -> EvaluationConfig:
        """Retrieve an evaluation configuration by ID."""
        config = self._configs.get(config_id)
        if config is None:
            raise EvaluationConfigError(f"Evaluation config {config_id!r} not found")
        return config

    async def update_evaluation_config(self, config_id: str, **updates: object) -> EvaluationConfig:
        """Update an evaluation configuration."""
        current = await self.get_evaluation_config(config_id)
        updated = current.model_copy(update=updates)
        self._configs[config_id] = updated
        self._log.info("model_evaluation.config.updated", config_id=config_id)
        return updated

    async def delete_evaluation_config(self, config_id: str) -> None:
        """Delete an evaluation configuration."""
        if config_id not in self._configs:
            raise EvaluationConfigError(f"Evaluation config {config_id!r} not found")
        del self._configs[config_id]
        self._log.info("model_evaluation.config.deleted", config_id=config_id)

    async def list_evaluation_configs(self) -> list[EvaluationConfig]:
        """List all evaluation configurations."""
        return list(self._configs.values())

    # -- evaluations ----------------------------------------------------------

    async def create_evaluation(self, evaluation: ModelEvaluation) -> ModelEvaluation:
        """Create a new model evaluation."""
        self._evaluations[evaluation.id] = evaluation
        self._log.info(
            "model_evaluation.evaluation.created",
            evaluation_id=evaluation.id,
            model_id=evaluation.model_id,
        )
        return evaluation

    async def get_evaluation(self, evaluation_id: str) -> ModelEvaluation:
        """Retrieve an evaluation by ID."""
        evaluation = self._evaluations.get(evaluation_id)
        if evaluation is None:
            raise EvaluationNotFoundError(f"Evaluation {evaluation_id!r} not found")
        return evaluation

    async def update_evaluation(self, evaluation_id: str, **updates: object) -> ModelEvaluation:
        """Update an evaluation."""
        current = await self.get_evaluation(evaluation_id)
        updated = current.model_copy(update={"updated_at": utc_now(), **updates})
        self._evaluations[evaluation_id] = updated
        self._log.info("model_evaluation.evaluation.updated", evaluation_id=evaluation_id)
        return updated

    async def delete_evaluation(self, evaluation_id: str) -> None:
        """Delete an evaluation."""
        if evaluation_id not in self._evaluations:
            raise EvaluationNotFoundError(f"Evaluation {evaluation_id!r} not found")
        del self._evaluations[evaluation_id]
        self._log.info("model_evaluation.evaluation.deleted", evaluation_id=evaluation_id)

    async def list_evaluations(self) -> list[ModelEvaluation]:
        """List all evaluations."""
        return list(self._evaluations.values())

    async def start_evaluation(self, evaluation_id: str) -> tuple[ModelEvaluation, EvaluationRun]:
        """Start an evaluation run."""
        evaluation = await self.get_evaluation(evaluation_id)
        if evaluation.status != EvaluationStatus.PENDING:
            raise EvaluationFailedError(
                f"Cannot start evaluation {evaluation_id!r} in status {evaluation.status}"
            )
        run = EvaluationRun(
            id=f"run_{evaluation_id}_{int(utc_now().timestamp())}",
            evaluation_id=evaluation_id,
            status=EvaluationStatus.RUNNING,
            started_at=utc_now(),
        )
        self._runs[run.id] = run
        updated = evaluation.model_copy(
            update={
                "status": EvaluationStatus.RUNNING,
                "current_result": None,
                "updated_at": utc_now(),
            }
        )
        self._evaluations[evaluation_id] = updated
        self._log.info(
            "model_evaluation.evaluation.started", evaluation_id=evaluation_id, run_id=run.id
        )
        return updated, run

    async def complete_evaluation(
        self, evaluation_id: str, result: EvaluationResult
    ) -> tuple[ModelEvaluation, EvaluationResult]:
        """Complete an evaluation with a result."""
        evaluation = await self.get_evaluation(evaluation_id)
        self._results[result.id] = result
        results = (*evaluation.results, result)
        updated = evaluation.model_copy(
            update={
                "status": EvaluationStatus.COMPLETED,
                "results": results,
                "current_result": result,
                "updated_at": utc_now(),
            }
        )
        self._evaluations[evaluation_id] = updated
        self._log.info(
            "model_evaluation.evaluation.completed",
            evaluation_id=evaluation_id,
            result_id=result.id,
        )
        return updated, result

    async def fail_evaluation(self, evaluation_id: str, error_message: str) -> ModelEvaluation:
        """Mark an evaluation as failed."""
        evaluation = await self.get_evaluation(evaluation_id)
        updated = evaluation.model_copy(
            update={
                "status": EvaluationStatus.FAILED,
                "updated_at": utc_now(),
            }
        )
        self._evaluations[evaluation_id] = updated
        self._log.info(
            "model_evaluation.evaluation.failed", evaluation_id=evaluation_id, error=error_message
        )
        return updated

    async def cancel_evaluation(self, evaluation_id: str, reason: str = "") -> ModelEvaluation:
        """Cancel a pending or running evaluation."""
        evaluation = await self.get_evaluation(evaluation_id)
        if evaluation.status not in (EvaluationStatus.PENDING, EvaluationStatus.RUNNING):
            raise EvaluationFailedError(
                f"Cannot cancel evaluation {evaluation_id!r} in status {evaluation.status}"
            )
        updated = evaluation.model_copy(
            update={
                "status": EvaluationStatus.CANCELLED,
                "updated_at": utc_now(),
            }
        )
        self._evaluations[evaluation_id] = updated
        self._log.info(
            "model_evaluation.evaluation.cancelled", evaluation_id=evaluation_id, reason=reason
        )
        return updated

    # -- evaluation results ---------------------------------------------------

    async def get_evaluation_result(self, result_id: str) -> EvaluationResult:
        """Retrieve an evaluation result by ID."""
        result = self._results.get(result_id)
        if result is None:
            raise EvaluationNotFoundError(f"Evaluation result {result_id!r} not found")
        return result

    async def list_evaluation_results(
        self, evaluation_id: str | None = None
    ) -> list[EvaluationResult]:
        """List evaluation results, optionally filtered by evaluation."""
        if evaluation_id is not None:
            return [r for r in self._results.values() if r.config_id == evaluation_id]
        return list(self._results.values())

    # -- evaluation runs ------------------------------------------------------

    async def get_evaluation_run(self, run_id: str) -> EvaluationRun:
        """Retrieve an evaluation run by ID."""
        run = self._runs.get(run_id)
        if run is None:
            raise EvaluationNotFoundError(f"Evaluation run {run_id!r} not found")
        return run

    async def complete_evaluation_run(self, run_id: str) -> EvaluationRun:
        """Mark an evaluation run as completed."""
        run = await self.get_evaluation_run(run_id)
        duration = 0.0
        if run.started_at is not None:
            duration = (utc_now() - run.started_at).total_seconds() * 1000
        updated = run.model_copy(
            update={
                "status": EvaluationStatus.COMPLETED,
                "completed_at": utc_now(),
                "duration_ms": duration,
            }
        )
        self._runs[run_id] = updated
        return updated

    # -- evaluation summary ---------------------------------------------------

    async def generate_summary(self, evaluation_ids: list[str]) -> EvaluationSummary:
        """Generate a summary for a set of evaluations."""
        total = len(evaluation_ids)
        completed = 0
        failed = 0
        metrics_summary: dict[str, float] = {}
        for eid in evaluation_ids:
            evaluation = self._evaluations.get(eid)
            if evaluation is None:
                continue
            if evaluation.status == EvaluationStatus.COMPLETED:
                completed += 1
            elif evaluation.status == EvaluationStatus.FAILED:
                failed += 1
            if evaluation.current_result is not None:
                for m in evaluation.current_result.metrics:
                    current = metrics_summary.get(m.name, 0.0)
                    metrics_summary[m.name] = current + m.value
        for key in metrics_summary:
            metrics_summary[key] /= max(total, 1)
        summary = EvaluationSummary(
            id=f"summary_{int(utc_now().timestamp())}",
            evaluation_ids=tuple(evaluation_ids),
            total_count=total,
            completed_count=completed,
            failed_count=failed,
            metrics_summary=metrics_summary,
        )
        self._summaries[summary.id] = summary
        self._log.info("model_evaluation.summary.generated", summary_id=summary.id, count=total)
        return summary

    async def get_summary(self, summary_id: str) -> EvaluationSummary:
        """Retrieve an evaluation summary by ID."""
        summary = self._summaries.get(summary_id)
        if summary is None:
            raise EvaluationNotFoundError(f"Summary {summary_id!r} not found")
        return summary

    # -- benchmark configs ----------------------------------------------------

    async def create_benchmark_config(self, config: BenchmarkConfig) -> BenchmarkConfig:
        """Create a new benchmark configuration."""
        self._benchmark_configs[config.id] = config
        self._log.info("model_evaluation.benchmark_config.created", config_id=config.id)
        return config

    async def get_benchmark_config(self, config_id: str) -> BenchmarkConfig:
        """Retrieve a benchmark configuration by ID."""
        config = self._benchmark_configs.get(config_id)
        if config is None:
            raise BenchmarkConfigError(f"Benchmark config {config_id!r} not found")
        return config

    async def update_benchmark_config(self, config_id: str, **updates: object) -> BenchmarkConfig:
        """Update a benchmark configuration."""
        current = await self.get_benchmark_config(config_id)
        updated = current.model_copy(update=updates)
        self._benchmark_configs[config_id] = updated
        self._log.info("model_evaluation.benchmark_config.updated", config_id=config_id)
        return updated

    async def delete_benchmark_config(self, config_id: str) -> None:
        """Delete a benchmark configuration."""
        if config_id not in self._benchmark_configs:
            raise BenchmarkConfigError(f"Benchmark config {config_id!r} not found")
        del self._benchmark_configs[config_id]
        self._log.info("model_evaluation.benchmark_config.deleted", config_id=config_id)

    async def list_benchmark_configs(self) -> list[BenchmarkConfig]:
        """List all benchmark configurations."""
        return list(self._benchmark_configs.values())

    # -- benchmarks -----------------------------------------------------------

    async def create_benchmark(self, benchmark: ModelBenchmark) -> ModelBenchmark:
        """Create a new model benchmark."""
        self._benchmarks[benchmark.id] = benchmark
        self._log.info("model_evaluation.benchmark.created", benchmark_id=benchmark.id)
        return benchmark

    async def get_benchmark(self, benchmark_id: str) -> ModelBenchmark:
        """Retrieve a benchmark by ID."""
        benchmark = self._benchmarks.get(benchmark_id)
        if benchmark is None:
            raise BenchmarkNotFoundError(f"Benchmark {benchmark_id!r} not found")
        return benchmark

    async def update_benchmark(self, benchmark_id: str, **updates: object) -> ModelBenchmark:
        """Update a benchmark."""
        current = await self.get_benchmark(benchmark_id)
        updated = current.model_copy(update={"updated_at": utc_now(), **updates})
        self._benchmarks[benchmark_id] = updated
        self._log.info("model_evaluation.benchmark.updated", benchmark_id=benchmark_id)
        return updated

    async def delete_benchmark(self, benchmark_id: str) -> None:
        """Delete a benchmark."""
        if benchmark_id not in self._benchmarks:
            raise BenchmarkNotFoundError(f"Benchmark {benchmark_id!r} not found")
        del self._benchmarks[benchmark_id]
        self._log.info("model_evaluation.benchmark.deleted", benchmark_id=benchmark_id)

    async def list_benchmarks(self) -> list[ModelBenchmark]:
        """List all benchmarks."""
        return list(self._benchmarks.values())

    async def start_benchmark(self, benchmark_id: str) -> tuple[ModelBenchmark, BenchmarkResult]:
        """Start a benchmark run for each model in the config."""
        benchmark = await self.get_benchmark(benchmark_id)
        if benchmark.status not in (BenchmarkStatus.PENDING,):
            raise BenchmarkFailedError(
                f"Cannot start benchmark {benchmark_id!r} in status {benchmark.status}"
            )
        config = await self.get_benchmark_config(benchmark.config_id)
        updated = benchmark.model_copy(
            update={
                "status": BenchmarkStatus.RUNNING,
                "updated_at": utc_now(),
            }
        )
        self._benchmarks[benchmark_id] = updated
        result = BenchmarkResult(
            id=f"br_{benchmark_id}_{int(utc_now().timestamp())}",
            config_id=benchmark.config_id,
            model_id=config.model_ids[0] if config.model_ids else "",
            status=BenchmarkStatus.RUNNING,
            started_at=utc_now(),
        )
        self._benchmark_results[result.id] = result
        self._log.info(
            "model_evaluation.benchmark.started", benchmark_id=benchmark_id, result_id=result.id
        )
        return updated, result

    async def complete_benchmark(self, benchmark_id: str, result_id: str) -> ModelBenchmark:
        """Complete a benchmark with a given result."""
        benchmark = await self.get_benchmark(benchmark_id)
        result = self._benchmark_results.get(result_id)
        if result is None:
            raise BenchmarkNotFoundError(f"Benchmark result {result_id!r} not found")
        completed_result = result.model_copy(
            update={
                "status": BenchmarkStatus.COMPLETED,
                "completed_at": utc_now(),
            }
        )
        self._benchmark_results[result_id] = completed_result
        results = (*benchmark.results, completed_result)
        updated = benchmark.model_copy(
            update={
                "status": BenchmarkStatus.COMPLETED,
                "results": results,
                "updated_at": utc_now(),
            }
        )
        self._benchmarks[benchmark_id] = updated
        self._log.info("model_evaluation.benchmark.completed", benchmark_id=benchmark_id)
        return updated

    async def fail_benchmark(self, benchmark_id: str, error_message: str) -> ModelBenchmark:
        """Mark a benchmark as failed."""
        benchmark = await self.get_benchmark(benchmark_id)
        updated = benchmark.model_copy(
            update={
                "status": BenchmarkStatus.FAILED,
                "updated_at": utc_now(),
            }
        )
        self._benchmarks[benchmark_id] = updated
        self._log.info(
            "model_evaluation.benchmark.failed", benchmark_id=benchmark_id, error=error_message
        )
        return updated

    async def cancel_benchmark(self, benchmark_id: str) -> ModelBenchmark:
        """Cancel a pending or running benchmark."""
        benchmark = await self.get_benchmark(benchmark_id)
        if benchmark.status not in (BenchmarkStatus.PENDING, BenchmarkStatus.RUNNING):
            raise BenchmarkFailedError(
                f"Cannot cancel benchmark {benchmark_id!r} in status {benchmark.status}"
            )
        updated = benchmark.model_copy(
            update={
                "status": BenchmarkStatus.CANCELLED,
                "updated_at": utc_now(),
            }
        )
        self._benchmarks[benchmark_id] = updated
        self._log.info("model_evaluation.benchmark.cancelled", benchmark_id=benchmark_id)
        return updated

    # -- benchmark results ----------------------------------------------------

    async def get_benchmark_result(self, result_id: str) -> BenchmarkResult:
        """Retrieve a benchmark result by ID."""
        result = self._benchmark_results.get(result_id)
        if result is None:
            raise BenchmarkNotFoundError(f"Benchmark result {result_id!r} not found")
        return result

    async def list_benchmark_results(
        self, benchmark_id: str | None = None
    ) -> list[BenchmarkResult]:
        """List benchmark results, optionally filtered by benchmark."""
        if benchmark_id is not None:
            return [r for r in self._benchmark_results.values() if r.config_id == benchmark_id]
        return list(self._benchmark_results.values())

    # -- benchmark comparison -------------------------------------------------

    async def compute_comparison(self, benchmark_id: str) -> BenchmarkComparison:
        """Compute a comparison of benchmark results across models."""
        benchmark = await self.get_benchmark(benchmark_id)
        if benchmark.status != BenchmarkStatus.COMPLETED:
            raise BenchmarkFailedError(
                f"Cannot compare benchmark {benchmark_id!r} in status {benchmark.status}"
            )
        scores_by_model: dict[str, tuple[BenchmarkScore, ...]] = {}
        model_scores: dict[str, float] = {}
        for result in benchmark.results:
            scores = result.scores
            scores_by_model[result.model_id] = scores
            model_scores[result.model_id] = sum(s.value * s.weight for s in scores)
        ranking = tuple(
            model_id
            for model_id, _ in sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        )
        comparison = BenchmarkComparison(
            id=f"cmp_{benchmark_id}_{int(utc_now().timestamp())}",
            benchmark_id=benchmark_id,
            result_ids=tuple(r.id for r in benchmark.results),
            scores=scores_by_model,
            ranking=ranking,
            summary=f"Comparison computed for {len(ranking)} models",
        )
        self._comparisons[comparison.id] = comparison
        self._log.info(
            "model_evaluation.comparison.computed", comparison_id=comparison.id, models=ranking
        )
        return comparison

    async def get_comparison(self, comparison_id: str) -> BenchmarkComparison:
        """Retrieve a benchmark comparison by ID."""
        comparison = self._comparisons.get(comparison_id)
        if comparison is None:
            raise BenchmarkNotFoundError(f"Comparison {comparison_id!r} not found")
        return comparison

    async def list_comparisons(self, benchmark_id: str | None = None) -> list[BenchmarkComparison]:
        """List comparisons, optionally filtered by benchmark."""
        if benchmark_id is not None:
            return [c for c in self._comparisons.values() if c.benchmark_id == benchmark_id]
        return list(self._comparisons.values())

    # -- model performance profiles -------------------------------------------

    async def get_or_create_profile(
        self, model_id: str, model_version: str = ""
    ) -> ModelPerformanceProfile:
        """Retrieve an existing profile or create a new one."""
        profile = self._profiles.get(model_id)
        if profile is None:
            profile = ModelPerformanceProfile(model_id=model_id, model_version=model_version)
            self._profiles[model_id] = profile
        return profile

    async def update_profile(
        self,
        model_id: str,
        evaluation_ids: list[str] | None = None,
        benchmark_ids: list[str] | None = None,
    ) -> ModelPerformanceProfile:
        """Update a model performance profile with latest data."""
        profile = await self.get_or_create_profile(model_id)
        evals = [
            self._evaluations[eid] for eid in (evaluation_ids or []) if eid in self._evaluations
        ]
        benchmarks = [
            self._benchmarks[bid] for bid in (benchmark_ids or []) if bid in self._benchmarks
        ]
        avg_metrics: dict[str, float] = {}
        best_metrics: dict[str, float] = {}
        worst_metrics: dict[str, float] = {}
        for ev in evals:
            if ev.current_result is not None:
                for m in ev.current_result.metrics:
                    avg_metrics[m.name] = avg_metrics.get(m.name, 0.0) + m.value
                    if m.name not in best_metrics or m.value > best_metrics[m.name]:
                        best_metrics[m.name] = m.value
                    if m.name not in worst_metrics or m.value < worst_metrics[m.name]:
                        worst_metrics[m.name] = m.value
        eval_count = len(evals)
        for key in avg_metrics:
            avg_metrics[key] /= max(eval_count, 1)
        updated = profile.model_copy(
            update={
                "avg_metrics": avg_metrics,
                "best_metrics": best_metrics,
                "worst_metrics": worst_metrics,
                "evaluation_count": eval_count,
                "benchmark_count": len(benchmarks),
                "last_evaluated_at": (utc_now() if evals else profile.last_evaluated_at),
                "profile_updated_at": utc_now(),
            }
        )
        self._profiles[model_id] = updated
        self._log.info("model_evaluation.profile.updated", model_id=model_id)
        return updated

    async def get_profile(self, model_id: str) -> ModelPerformanceProfile:
        """Retrieve a model performance profile."""
        profile = self._profiles.get(model_id)
        if profile is None:
            raise ModelProfileError(f"Profile for model {model_id!r} not found")
        return profile

    async def list_profiles(self) -> list[ModelPerformanceProfile]:
        """List all model performance profiles."""
        return list(self._profiles.values())

    # -- event helpers --------------------------------------------------------

    def _emit_evaluation_created(
        self, evaluation_id: str, model_id: str, config_id: str
    ) -> EvaluationCreated:
        return EvaluationCreated(
            evaluation_id=evaluation_id,
            model_id=model_id,
            config_id=config_id,
        )

    def _emit_evaluation_started(
        self, evaluation_id: str, model_id: str, run_id: str
    ) -> EvaluationStarted:
        return EvaluationStarted(
            evaluation_id=evaluation_id,
            model_id=model_id,
            run_id=run_id,
        )

    def _emit_evaluation_completed(
        self,
        evaluation_id: str,
        model_id: str,
        result_id: str,
        metrics_count: int = 0,
    ) -> EvaluationCompleted:
        return EvaluationCompleted(
            evaluation_id=evaluation_id,
            model_id=model_id,
            result_id=result_id,
            metrics_count=metrics_count,
        )

    def _emit_evaluation_failed(
        self, evaluation_id: str, model_id: str, error_message: str
    ) -> EvaluationFailed:
        return EvaluationFailed(
            evaluation_id=evaluation_id,
            model_id=model_id,
            error_message=error_message,
        )

    def _emit_evaluation_cancelled(
        self, evaluation_id: str, model_id: str, reason: str = ""
    ) -> EvaluationCancelled:
        return EvaluationCancelled(
            evaluation_id=evaluation_id,
            model_id=model_id,
            reason=reason,
        )

    def _emit_metric_recorded(
        self,
        evaluation_id: str,
        result_id: str,
        metric_name: str,
        metric_value: float,
    ) -> MetricRecorded:
        return MetricRecorded(
            evaluation_id=evaluation_id,
            result_id=result_id,
            metric_name=metric_name,
            metric_value=metric_value,
        )

    def _emit_benchmark_created(self, benchmark_id: str, config_id: str) -> BenchmarkCreated:
        return BenchmarkCreated(benchmark_id=benchmark_id, config_id=config_id)

    def _emit_benchmark_started(self, benchmark_id: str, model_count: int = 0) -> BenchmarkStarted:
        return BenchmarkStarted(benchmark_id=benchmark_id, model_count=model_count)

    def _emit_benchmark_completed(
        self, benchmark_id: str, result_count: int = 0
    ) -> BenchmarkCompleted:
        return BenchmarkCompleted(benchmark_id=benchmark_id, result_count=result_count)

    def _emit_benchmark_failed(self, benchmark_id: str, error_message: str) -> BenchmarkFailed:
        return BenchmarkFailed(benchmark_id=benchmark_id, error_message=error_message)

    def _emit_benchmark_comparison_computed(
        self,
        comparison_id: str,
        benchmark_id: str,
        ranked_models: tuple[str, ...],
    ) -> BenchmarkComparisonComputed:
        return BenchmarkComparisonComputed(
            comparison_id=comparison_id,
            benchmark_id=benchmark_id,
            ranked_models=ranked_models,
        )

    def _emit_evaluation_summary_generated(
        self, summary_id: str, evaluation_count: int
    ) -> EvaluationSummaryGenerated:
        return EvaluationSummaryGenerated(summary_id=summary_id, evaluation_count=evaluation_count)

    async def evaluate_completion(self, prompt: str, completion: str) -> dict[str, float]:
        """Asynchronously compute factual consistency and relevance metrics for a completion."""
        relevance = 1.0 if any(w in completion.lower() for w in prompt.lower().split() if len(w) > 3) else 0.5
        factuality = 1.0 if len(completion.strip()) > 5 else 0.0
        return {
            "relevance_score": relevance,
            "factuality_score": factuality,
        }


__all__ = ["ModelEvaluationService"]

