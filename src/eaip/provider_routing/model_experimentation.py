"""Model experimentation — A/B testing and traffic splitting for models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ExperimentStatus(StrEnum):
    """Experiment lifecycle status."""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ModelExperiment(BaseModel):
    """An A/B experiment across multiple models."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    name: str
    models: list[str] = Field(description="Model IDs participating")
    task_type: str = ""
    traffic_split: dict[str, float] = Field(default_factory=dict, description="model_id -> percentage")
    status: ExperimentStatus = ExperimentStatus.DRAFT
    winner: str = ""
    created_at: Any = Field(default_factory=utc_now)
    updated_at: Any = Field(default_factory=utc_now)


class ExperimentResult(BaseModel):
    """A single result within an experiment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    experiment_id: str
    model_id: str
    tenant_id: str
    quality: float = Field(ge=0.0, le=1.0)
    latency_ms: float = 0.0
    cost: float = 0.0
    success: bool = True
    recorded_at: Any = Field(default_factory=utc_now)


class ExperimentSummary(BaseModel):
    """Summary of experiment results."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    experiment_id: str
    status: ExperimentStatus
    models: dict[str, dict[str, Any]] = Field(default_factory=dict)
    winner: str = ""
    recommendation: str = ""


class ModelExperimentManager:
    """Manage A/B experiments across models.

    Never silently routes production traffic into unapproved models.
    All traffic splits are explicit and logged.
    """

    def __init__(self) -> None:
        self._experiments: dict[str, ModelExperiment] = {}
        self._results: list[ExperimentResult] = []
        self._log = get_logger("eaip.provider_routing.model_experiment")

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        tenant_id: str,
        models: list[str],
        task_type: str,
        traffic_split: dict[str, float] | None = None,
    ) -> ModelExperiment:
        """Create a new experiment."""
        if not traffic_split:
            pct = 1.0 / len(models) if models else 0.0
            traffic_split = {m: pct for m in models}

        total = sum(traffic_split.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")

        experiment = ModelExperiment(
            id=experiment_id,
            tenant_id=tenant_id,
            name=name,
            models=models,
            task_type=task_type,
            traffic_split=traffic_split,
            status=ExperimentStatus.DRAFT,
        )
        self._experiments[f"{tenant_id}:{experiment_id}"] = experiment
        self._log.info("experiment.created", experiment_id=experiment_id, models=models)
        return experiment

    def start_experiment(self, experiment_id: str, tenant_id: str) -> ModelExperiment:
        """Start an experiment."""
        key = f"{tenant_id}:{experiment_id}"
        exp = self._experiments.get(key)
        if exp is None:
            raise ValueError(f"Experiment {experiment_id} not found")
        updated = exp.model_copy(update={"status": ExperimentStatus.RUNNING, "updated_at": utc_now()})
        self._experiments[key] = updated
        self._log.info("experiment.started", experiment_id=experiment_id)
        return updated

    def record_result(self, result: ExperimentResult) -> ExperimentResult:
        """Record a result for an experiment."""
        self._results.append(result)
        self._log.info(
            "experiment.result_recorded",
            experiment_id=result.experiment_id,
            model_id=result.model_id,
            quality=result.quality,
        )
        return result

    def get_experiment_results(self, experiment_id: str, tenant_id: str) -> ExperimentSummary:
        """Get aggregated results for an experiment."""
        exp = self._experiments.get(f"{tenant_id}:{experiment_id}")
        if exp is None:
            return ExperimentSummary(experiment_id=experiment_id, status=ExperimentStatus.DRAFT)

        results = [r for r in self._results if r.experiment_id == experiment_id and r.tenant_id == tenant_id]
        model_stats: dict[str, dict[str, Any]] = {}
        for model_id in exp.models:
            mr = [r for r in results if r.model_id == model_id]
            if mr:
                avg_q = sum(r.quality for r in mr) / len(mr)
                avg_l = sum(r.latency_ms for r in mr) / len(mr)
                avg_c = sum(r.cost for r in mr) / len(mr)
                sr = sum(1 for r in mr if r.success) / len(mr)
                model_stats[model_id] = {
                    "evaluations": len(mr),
                    "avg_quality": round(avg_q, 3),
                    "avg_latency_ms": round(avg_l, 1),
                    "avg_cost": round(avg_c, 4),
                    "success_rate": round(sr, 3),
                }

        best_model = ""
        best_quality = 0.0
        for mid, stats in model_stats.items():
            if stats["avg_quality"] > best_quality:
                best_quality = stats["avg_quality"]
                best_model = mid

        return ExperimentSummary(
            experiment_id=experiment_id,
            status=exp.status,
            models=model_stats,
            winner=exp.winner or best_model,
            recommendation=f"Best quality: {best_model} ({best_quality:.3f})" if best_model else "Insufficient data",
        )

    def promote_winner(self, experiment_id: str, tenant_id: str, model_id: str) -> ModelExperiment:
        """Promote a model as the experiment winner."""
        key = f"{tenant_id}:{experiment_id}"
        exp = self._experiments.get(key)
        if exp is None:
            raise ValueError(f"Experiment {experiment_id} not found")
        updated = exp.model_copy(update={
            "winner": model_id,
            "status": ExperimentStatus.COMPLETED,
            "updated_at": utc_now(),
        })
        self._experiments[key] = updated
        self._log.info("experiment.winner_promoted", experiment_id=experiment_id, winner=model_id)
        return updated

    def list_experiments(self, tenant_id: str) -> list[ModelExperiment]:
        """List all experiments for a tenant."""
        return [v for k, v in self._experiments.items() if k.startswith(f"{tenant_id}:")]


__all__ = [
    "ExperimentResult",
    "ExperimentStatus",
    "ExperimentSummary",
    "ModelExperiment",
    "ModelExperimentManager",
]
