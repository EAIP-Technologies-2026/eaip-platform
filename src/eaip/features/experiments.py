"""Experiment service — create, manage, and analyze A/B experiments."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

try:
    from scipy import stats as _sp_stats  # type: ignore[import-untyped]

    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False

from eaip.features.events import (
    ExperimentCompleted,
    ExperimentCreated,
    ExperimentResultRecorded,
    ExperimentStarted,
    VariantAssigned,
)
from eaip.features.exceptions import ExperimentCompleteError, ExperimentNotFoundError
from eaip.features.models import Experiment, ExperimentResult, ExperimentStatus, ExperimentVariant
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


class ExperimentService:
    """Manages A/B experiment lifecycle and statistical analysis."""

    def __init__(self, event_callback: EventCallback | None = None) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._results: list[ExperimentResult] = []
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    async def create_experiment(
        self,
        id: str,
        name: str,
        feature_key: str,
        description: str = "",
        variants: tuple[ExperimentVariant, ...] = (),
        traffic_allocation: dict[str, int] | None = None,
        metrics: tuple[str, ...] = (),
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Experiment:
        exp = Experiment(
            id=id,
            name=name,
            description=description,
            feature_key=feature_key,
            variants=variants,
            traffic_allocation=traffic_allocation or {},
            status=ExperimentStatus.DRAFT,
            metrics=metrics,
            start_at=start_at,
            end_at=end_at,
            metadata=metadata or {},
        )
        self._experiments[id] = exp
        self._emit(
            ExperimentCreated(
                experiment_id=id,
                name=name,
                feature_key=feature_key,
            )
        )
        return exp

    async def get_experiment(self, experiment_id: str) -> Experiment:
        if experiment_id not in self._experiments:
            raise ExperimentNotFoundError(
                f"Experiment not found: {experiment_id}", context={"experiment_id": experiment_id}
            )
        return self._experiments[experiment_id]

    async def update_experiment(
        self,
        experiment_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        variants: tuple[ExperimentVariant, ...] | None = None,
        traffic_allocation: dict[str, int] | None = None,
        metrics: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Experiment:
        exp = await self.get_experiment(experiment_id)
        if exp.status == ExperimentStatus.COMPLETED:
            raise ExperimentCompleteError(
                f"Cannot update completed experiment: {experiment_id}",
                context={"experiment_id": experiment_id},
            )

        updated = Experiment(
            id=exp.id,
            name=name or exp.name,
            description=description if description is not None else exp.description,
            feature_key=exp.feature_key,
            variants=variants if variants is not None else exp.variants,
            traffic_allocation=(
                traffic_allocation if traffic_allocation is not None else exp.traffic_allocation
            ),
            status=exp.status,
            metrics=metrics if metrics is not None else exp.metrics,
            start_at=exp.start_at,
            end_at=exp.end_at,
            metadata=metadata if metadata is not None else exp.metadata,
        )
        self._experiments[experiment_id] = updated
        return updated

    async def start_experiment(self, experiment_id: str) -> Experiment:
        exp = await self.get_experiment(experiment_id)
        if exp.status == ExperimentStatus.COMPLETED:
            raise ExperimentCompleteError(
                f"Cannot start completed experiment: {experiment_id}",
                context={"experiment_id": experiment_id},
            )
        now = utc_now()
        updated = Experiment(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            feature_key=exp.feature_key,
            variants=exp.variants,
            traffic_allocation=exp.traffic_allocation,
            status=ExperimentStatus.RUNNING,
            metrics=exp.metrics,
            start_at=exp.start_at or now,
            end_at=exp.end_at,
            metadata=exp.metadata,
        )
        self._experiments[experiment_id] = updated
        self._emit(ExperimentStarted(experiment_id=experiment_id, feature_key=exp.feature_key))
        return updated

    async def pause_experiment(self, experiment_id: str) -> Experiment:
        exp = await self.get_experiment(experiment_id)
        if exp.status == ExperimentStatus.COMPLETED:
            raise ExperimentCompleteError(
                f"Cannot pause completed experiment: {experiment_id}",
                context={"experiment_id": experiment_id},
            )
        updated = Experiment(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            feature_key=exp.feature_key,
            variants=exp.variants,
            traffic_allocation=exp.traffic_allocation,
            status=ExperimentStatus.PAUSED,
            metrics=exp.metrics,
            start_at=exp.start_at,
            end_at=exp.end_at,
            metadata=exp.metadata,
        )
        self._experiments[experiment_id] = updated
        return updated

    async def complete_experiment(self, experiment_id: str) -> Experiment:
        exp = await self.get_experiment(experiment_id)
        now = utc_now()
        updated = Experiment(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            feature_key=exp.feature_key,
            variants=exp.variants,
            traffic_allocation=exp.traffic_allocation,
            status=ExperimentStatus.COMPLETED,
            metrics=exp.metrics,
            start_at=exp.start_at,
            end_at=exp.end_at or now,
            metadata=exp.metadata,
        )
        self._experiments[experiment_id] = updated
        self._emit(ExperimentCompleted(experiment_id=experiment_id, feature_key=exp.feature_key))
        return updated

    async def assign_variant(self, experiment_id: str, entity_id: str) -> ExperimentVariant:
        exp = await self.get_experiment(experiment_id)
        if exp.status != ExperimentStatus.RUNNING:
            raise ExperimentCompleteError(
                f"Experiment {experiment_id} is not running",
                context={"experiment_id": experiment_id, "status": str(exp.status)},
            )
        if not exp.variants:
            raise ValueError(f"Experiment {experiment_id} has no variants")

        variant = exp.variants[0]
        self._emit(
            VariantAssigned(
                experiment_id=experiment_id,
                variant_id=variant.id,
                entity_id=entity_id,
            )
        )
        return variant

    async def record_result(
        self,
        id: str,
        experiment_id: str,
        variant_id: str,
        metric_name: str,
        metric_value: float,
        sample_size: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ExperimentResult:
        exp = await self.get_experiment(experiment_id)
        result = ExperimentResult(
            id=id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            metric_name=metric_name,
            metric_value=metric_value,
            sample_size=sample_size,
            started_at=exp.start_at or utc_now(),
            metadata=metadata or {},
        )
        self._results.append(result)
        self._emit(
            ExperimentResultRecorded(
                experiment_id=experiment_id,
                result_id=id,
                metric_name=metric_name,
                metric_value=metric_value,
            )
        )
        return result

    async def get_results(self, experiment_id: str) -> list[ExperimentResult]:
        await self.get_experiment(experiment_id)
        return [r for r in self._results if r.experiment_id == experiment_id]

    async def list_experiments(self) -> list[Experiment]:
        return list(self._experiments.values())

    async def analyze_results(self, experiment_id: str) -> dict[str, Any]:
        """Run statistical analysis on experiment results using chi-squared test."""
        if not _HAS_SCIPY:
            return {
                "experiment_id": experiment_id,
                "conclusive": False,
                "reason": "scipy is required for statistical analysis",
            }

        exp = await self.get_experiment(experiment_id)
        results = [r for r in self._results if r.experiment_id == experiment_id]

        if len(results) < 2:
            return {
                "experiment_id": experiment_id,
                "conclusive": False,
                "reason": "Insufficient results data for analysis",
            }

        variant_names = {v.id: v.name for v in exp.variants}
        metrics = list({r.metric_name for r in results})

        analysis: dict[str, Any] = {
            "experiment_id": experiment_id,
            "conclusive": True,
            "variants": {},
            "metrics": {},
        }

        for metric in metrics:
            metric_results = [r for r in results if r.metric_name == metric]
            if len(metric_results) < 2:
                analysis["metrics"][metric] = {
                    "conclusive": False,
                    "reason": "Insufficient data per variant",
                }
                continue

            control = metric_results[0]
            treatment = metric_results[1]

            observed = [
                [control.sample_size, treatment.sample_size],
                [
                    int(control.metric_value * control.sample_size),
                    int(treatment.metric_value * treatment.sample_size),
                ],
            ]

            try:
                chi2, p_value, dof, _expected = _sp_stats.chi2_contingency(observed)
                significant = p_value < 0.05

                result_entry = {
                    "chi2": float(chi2),
                    "p_value": float(p_value),
                    "degrees_of_freedom": int(dof),
                    "significant": bool(significant),
                }

                analysis["metrics"][metric] = result_entry

                if significant:
                    lift = (
                        (treatment.metric_value - control.metric_value) / control.metric_value * 100
                        if control.metric_value != 0
                        else 0.0
                    )
                    winner = treatment.variant_id if lift > 0 else control.variant_id
                    analysis["winner_variant_id"] = winner
                    analysis["winner_variant_name"] = variant_names.get(winner, winner)
                    analysis["lift_percentage"] = round(abs(lift), 2)

            except Exception as exc:
                analysis["metrics"][metric] = {
                    "conclusive": False,
                    "error": str(exc),
                }

        return analysis


__all__ = ["ExperimentService"]
