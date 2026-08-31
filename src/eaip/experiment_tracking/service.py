"""ExperimentTrackingService — CRUD experiments, runs, analysis, comparisons, and reports."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any

from eaip.experiment_tracking.exceptions import (
    ExperimentActivationError,
    ExperimentAnalysisError,
    ExperimentAssignmentError,
    ExperimentConfigError,
    ExperimentNotFoundError,
    ExperimentRunError,
)
from eaip.experiment_tracking.models import (
    Experiment,
    ExperimentAssignment,
    ExperimentAuditLog,
    ExperimentComparison,
    ExperimentConfig,
    ExperimentHypothesis,
    ExperimentMetric,
    ExperimentReport,
    ExperimentResult,
    ExperimentRun,
    ExperimentRunStatus,
    ExperimentStatus,
    ExperimentVariant,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ExperimentTrackingService:
    """Central service for managing experiments, runs, and statistical analysis."""

    def __init__(self, config: ExperimentConfig | None = None) -> None:
        self._config = config or ExperimentConfig()
        self._experiments: dict[str, Experiment] = {}
        self._assignments: dict[str, list[ExperimentAssignment]] = defaultdict(list)
        self._audit_logs: dict[str, list[ExperimentAuditLog]] = defaultdict(list)
        self._log = get_logger("eaip.experiment_tracking.service")

    @property
    def config(self) -> ExperimentConfig:
        return self._config

    # -- Experiment CRUD ---------------------------------------------------

    async def create_experiment(
        self,
        name: str,
        description: str = "",
        variants: tuple[ExperimentVariant, ...] = (),
        metrics: tuple[ExperimentMetric, ...] = (),
        hypothesis: ExperimentHypothesis | None = None,
        config: ExperimentConfig | None = None,
    ) -> Experiment:
        experiment_id = f"exp_{utc_now().timestamp():.0f}"
        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            variants=variants,
            metrics=metrics,
            hypothesis=hypothesis,
            config=config or self._config,
        )
        self._experiments[experiment_id] = experiment
        self._log.info("experiment.created", experiment_id=experiment_id, name=name)
        return experiment

    async def get_experiment(self, experiment_id: str) -> Experiment:
        experiment = self._experiments.get(experiment_id)
        if experiment is None:
            raise ExperimentNotFoundError(experiment_id)
        return experiment

    async def list_experiments(self, status: ExperimentStatus | None = None) -> list[Experiment]:
        result = list(self._experiments.values())
        if status:
            result = [e for e in result if e.status == status]
        return result

    async def update_experiment(self, experiment_id: str, **updates: Any) -> Experiment:
        experiment = await self.get_experiment(experiment_id)
        updated = experiment.model_copy(update=dict(updates, updated_at=utc_now()))
        self._experiments[experiment_id] = updated
        self._log.info("experiment.updated", experiment_id=experiment_id)
        return updated

    async def delete_experiment(self, experiment_id: str) -> None:
        if experiment_id not in self._experiments:
            raise ExperimentNotFoundError(experiment_id)
        del self._experiments[experiment_id]
        self._assignments.pop(experiment_id, None)
        self._audit_logs.pop(experiment_id, None)
        self._log.info("experiment.deleted", experiment_id=experiment_id)

    # -- Experiment lifecycle ---------------------------------------------

    async def activate_experiment(self, experiment_id: str) -> Experiment:
        experiment = await self.get_experiment(experiment_id)
        if experiment.status != ExperimentStatus.DRAFT:
            raise ExperimentActivationError(
                f"cannot activate experiment in status {experiment.status.value}"
            )
        if not experiment.variants:
            raise ExperimentActivationError("experiment must have at least one variant")
        if not experiment.metrics:
            raise ExperimentActivationError("experiment must have at least one metric")
        return await self.update_experiment(experiment_id, status=ExperimentStatus.ACTIVE)

    async def pause_experiment(self, experiment_id: str) -> Experiment:
        experiment = await self.get_experiment(experiment_id)
        if experiment.status != ExperimentStatus.ACTIVE:
            raise ExperimentActivationError(
                f"cannot pause experiment in status {experiment.status.value}"
            )
        return await self.update_experiment(experiment_id, status=ExperimentStatus.PAUSED)

    async def complete_experiment(self, experiment_id: str) -> Experiment:
        experiment = await self.get_experiment(experiment_id)
        if experiment.status not in (ExperimentStatus.ACTIVE, ExperimentStatus.PAUSED):
            raise ExperimentActivationError(
                f"cannot complete experiment in status {experiment.status.value}"
            )
        return await self.update_experiment(experiment_id, status=ExperimentStatus.COMPLETED)

    async def cancel_experiment(self, experiment_id: str) -> Experiment:
        experiment = await self.get_experiment(experiment_id)
        if experiment.status == ExperimentStatus.COMPLETED:
            raise ExperimentActivationError("cannot cancel a completed experiment")
        return await self.update_experiment(experiment_id, status=ExperimentStatus.CANCELLED)

    # -- Variants ---------------------------------------------------------

    async def add_variant(self, experiment_id: str, variant: ExperimentVariant) -> Experiment:
        experiment = await self.get_experiment(experiment_id)
        if any(v.id == variant.id for v in experiment.variants):
            raise ExperimentConfigError(f"variant {variant.id!r} already exists")
        new_variants = (*experiment.variants, variant)
        return await self.update_experiment(experiment_id, variants=new_variants)

    async def remove_variant(self, experiment_id: str, variant_id: str) -> Experiment:
        experiment = await self.get_experiment(experiment_id)
        new_variants = tuple(v for v in experiment.variants if v.id != variant_id)
        if len(new_variants) == len(experiment.variants):
            raise ExperimentNotFoundError(variant_id)
        return await self.update_experiment(experiment_id, variants=new_variants)

    # -- Runs -------------------------------------------------------------

    async def start_run(self, experiment_id: str, variant_id: str) -> ExperimentRun:
        experiment = await self.get_experiment(experiment_id)
        if experiment.status != ExperimentStatus.ACTIVE:
            raise ExperimentRunError("experiment is not active")
        if not any(v.id == variant_id for v in experiment.variants):
            raise ExperimentNotFoundError(variant_id)
        run = ExperimentRun(
            id=f"run_{utc_now().timestamp():.0f}",
            experiment_id=experiment_id,
            status=ExperimentRunStatus.RUNNING,
            variant_id=variant_id,
            started_at=utc_now(),
        )
        new_runs = (*experiment.runs, run)
        await self.update_experiment(experiment_id, runs=new_runs)
        self._log.info("experiment.run.started", run_id=run.id, experiment_id=experiment_id)
        return run

    async def complete_run(
        self,
        experiment_id: str,
        run_id: str,
        results: tuple[ExperimentResult, ...] = (),
    ) -> ExperimentRun:
        experiment = await self.get_experiment(experiment_id)
        run = self._find_run(experiment, run_id)
        if run.status != ExperimentRunStatus.RUNNING:
            raise ExperimentRunError(f"run {run_id} is not running")
        completed = run.model_copy(
            update={
                "status": ExperimentRunStatus.COMPLETED,
                "completed_at": utc_now(),
                "results": results,
            }
        )
        updated_runs = tuple(completed if r.id == run_id else r for r in experiment.runs)
        await self.update_experiment(experiment_id, runs=updated_runs)
        self._log.info("experiment.run.completed", run_id=run_id, experiment_id=experiment_id)
        return completed

    async def fail_run(
        self, experiment_id: str, run_id: str, error_message: str = ""
    ) -> ExperimentRun:
        experiment = await self.get_experiment(experiment_id)
        run = self._find_run(experiment, run_id)
        if run.status != ExperimentRunStatus.RUNNING:
            raise ExperimentRunError(f"run {run_id} is not running")
        failed = run.model_copy(
            update={
                "status": ExperimentRunStatus.FAILED,
                "completed_at": utc_now(),
                "error_message": error_message,
            }
        )
        updated_runs = tuple(failed if r.id == run_id else r for r in experiment.runs)
        await self.update_experiment(experiment_id, runs=updated_runs)
        self._log.info("experiment.run.failed", run_id=run_id, experiment_id=experiment_id)
        return failed

    def _find_run(self, experiment: Experiment, run_id: str) -> ExperimentRun:
        for run in experiment.runs:
            if run.id == run_id:
                return run
        raise ExperimentNotFoundError(run_id)

    # -- Analysis ---------------------------------------------------------

    async def compute_comparison(
        self,
        experiment_id: str,
        control_variant_id: str,
        treatment_variant_id: str,
        metric_id: str,
    ) -> ExperimentComparison:
        experiment = await self.get_experiment(experiment_id)
        control_results = self._collect_results(experiment, control_variant_id, metric_id)
        treatment_results = self._collect_results(experiment, treatment_variant_id, metric_id)

        if not control_results or not treatment_results:
            raise ExperimentAnalysisError("insufficient data for comparison")

        control_mean = sum(control_results) / len(control_results)
        treatment_mean = sum(treatment_results) / len(treatment_results)

        lift = (treatment_mean - control_mean) / control_mean if control_mean != 0 else 0.0

        p_value = self._compute_p_value(control_results, treatment_results)
        significant = p_value < (1.0 - experiment.config.confidence_level)

        comparison = ExperimentComparison(
            id=f"cmp_{utc_now().timestamp():.0f}",
            experiment_id=experiment_id,
            control_variant_id=control_variant_id,
            treatment_variant_id=treatment_variant_id,
            metric_id=metric_id,
            lift=round(lift, 6),
            p_value=round(p_value, 6),
            significant=significant,
            confidence_level=experiment.config.confidence_level,
            sample_size_control=len(control_results),
            sample_size_treatment=len(treatment_results),
        )
        self._log.info(
            "experiment.comparison.computed",
            experiment_id=experiment_id,
            comparison_id=comparison.id,
        )
        return comparison

    def _collect_results(
        self, experiment: Experiment, variant_id: str, metric_id: str
    ) -> list[float]:
        values: list[float] = []
        for run in experiment.runs:
            if run.variant_id == variant_id:
                values.extend(r.mean for r in run.results if r.metric_id == metric_id)
        return values

    def _compute_p_value(self, control: list[float], treatment: list[float]) -> float:
        n1, n2 = len(control), len(treatment)
        if n1 < 2 or n2 < 2:
            return 1.0
        mean1 = statistics.mean(control)
        mean2 = statistics.mean(treatment)
        var1 = statistics.variance(control, mean1)
        var2 = statistics.variance(treatment, mean2)

        se = math.sqrt(var1 / n1 + var2 / n2)
        if se == 0:
            return 1.0
        t_stat = (mean2 - mean1) / se
        df = min(n1 - 1, n2 - 1)
        p = self._t_distribution_cdf(-abs(t_stat), df) * 2
        return min(max(p, 0.0), 1.0)

    @staticmethod
    def _t_distribution_cdf(x: float, df: int) -> float:

        try:
            from scipy import stats  # type: ignore[import-untyped]

            return float(stats.t.cdf(x, df))
        except ImportError:
            pass
        x = max(min(x, 10.0), -10.0)
        a = df / 2.0
        b = 0.5
        z = df / (df + x * x)
        try:
            from scipy.special import betainc  # type: ignore[import-untyped]

            return float(1.0 - 0.5 * betainc(a, b, z))
        except ImportError:
            pass
        if x > 0:
            return 1.0 - 0.5 * math.exp(-x * x / 2)
        return 0.5 * math.exp(-x * x / 2)

    async def test_hypothesis(self, experiment_id: str) -> ExperimentHypothesis:
        experiment = await self.get_experiment(experiment_id)
        if experiment.hypothesis is None:
            raise ExperimentAnalysisError("experiment has no hypothesis")
        hypothesis = experiment.hypothesis
        if not experiment.variants:
            raise ExperimentAnalysisError("experiment has no variants")

        control_id = experiment.variants[0].id
        treatment_ids = [v.id for v in experiment.variants[1:]]
        if not treatment_ids:
            raise ExperimentAnalysisError("experiment has no treatment variants")

        comparison = await self.compute_comparison(
            experiment_id=experiment_id,
            control_variant_id=control_id,
            treatment_variant_id=treatment_ids[0],
            metric_id=hypothesis.metric_id,
        )

        tested = hypothesis.model_copy(
            update={
                "tested": True,
                "accepted": comparison.significant,
                "p_value": comparison.p_value,
            }
        )
        updated_experiment = await self.update_experiment(experiment_id, hypothesis=tested)
        assert updated_experiment.hypothesis is not None
        self._log.info(
            "experiment.hypothesis.tested",
            experiment_id=experiment_id,
            hypothesis_id=tested.id,
        )
        return updated_experiment.hypothesis

    # -- Reports ----------------------------------------------------------

    async def generate_report(
        self,
        experiment_id: str,
        comparisons: tuple[ExperimentComparison, ...] = (),
    ) -> ExperimentReport:
        experiment = await self.get_experiment(experiment_id)
        hypotheses: tuple[ExperimentHypothesis, ...] = ()
        if experiment.hypothesis:
            hypotheses = (experiment.hypothesis,)
        report = ExperimentReport(
            id=f"rpt_{utc_now().timestamp():.0f}",
            experiment_id=experiment_id,
            title=f"Report: {experiment.name}",
            summary=f"Experiment report for {experiment.name} "
            f"({len(experiment.runs)} runs, {len(comparisons)} comparisons)",
            comparisons=comparisons,
            hypotheses=hypotheses,
        )
        self._log.info(
            "experiment.report.generated",
            experiment_id=experiment_id,
            report_id=report.id,
        )
        return report

    # -- Assignments ------------------------------------------------------

    async def log_assignment(
        self,
        experiment_id: str,
        variant_id: str,
        entity_id: str,
        context: dict[str, Any] | None = None,
    ) -> ExperimentAssignment:
        experiment = await self.get_experiment(experiment_id)
        if experiment.status != ExperimentStatus.ACTIVE:
            raise ExperimentAssignmentError("experiment is not active")
        if not any(v.id == variant_id for v in experiment.variants):
            raise ExperimentNotFoundError(variant_id)
        assignment = ExperimentAssignment(
            experiment_id=experiment_id,
            variant_id=variant_id,
            entity_id=entity_id,
            context=context or {},
        )
        self._assignments[experiment_id].append(assignment)
        return assignment

    # -- Audit logs -------------------------------------------------------

    async def log_audit(
        self,
        experiment_id: str,
        action: str,
        actor: str = "",
        details: dict[str, Any] | None = None,
    ) -> ExperimentAuditLog:
        await self.get_experiment(experiment_id)
        log = ExperimentAuditLog(
            id=f"audit_{utc_now().timestamp():.0f}_{action}",
            experiment_id=experiment_id,
            action=action,
            actor=actor,
            details=details or {},
        )
        self._audit_logs[experiment_id].append(log)
        return log

    async def get_audit_logs(self, experiment_id: str) -> list[ExperimentAuditLog]:
        await self.get_experiment(experiment_id)
        return list(self._audit_logs.get(experiment_id, []))


__all__ = ["ExperimentTrackingService"]
