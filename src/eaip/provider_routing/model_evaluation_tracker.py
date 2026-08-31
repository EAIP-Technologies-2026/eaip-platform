"""Model evaluation tracker — track and compare model performance."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ModelEvaluationRecord(BaseModel):
    """A single model evaluation record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    tenant_id: str
    task_type: str
    quality_score: float = Field(ge=0.0, le=1.0)
    latency_ms: float = 0.0
    cost: float = 0.0
    success: bool = True
    evaluated_at: Any = Field(default_factory=utc_now)


class ModelPerformanceMetrics(BaseModel):
    """Aggregated performance metrics for a model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    tenant_id: str
    total_evaluations: int = 0
    avg_quality: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost: float = 0.0
    success_rate: float = 0.0
    task_type_breakdown: dict[str, dict[str, float]] = Field(default_factory=dict)


class ModelComparison(BaseModel):
    """Comparison of multiple models on a task type."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_type: str
    models: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str = ""


class ModelEvaluationTracker:
    """Track model evaluation results and feed into model_evaluation/service.py."""

    def __init__(self) -> None:
        self._evaluations: list[ModelEvaluationRecord] = []
        self._log = get_logger("eaip.provider_routing.model_eval_tracker")

    async def track_evaluation(self, record: ModelEvaluationRecord) -> ModelEvaluationRecord:
        """Record a model evaluation result."""
        self._evaluations.append(record)
        self._log.info(
            "model.eval.tracked",
            model_id=record.model_id,
            task_type=record.task_type,
            quality=record.quality_score,
            success=record.success,
        )
        return record

    async def get_model_performance(
        self, model_id: str, tenant_id: str
    ) -> ModelPerformanceMetrics:
        """Get aggregated performance metrics for a model."""
        records = [
            r for r in self._evaluations
            if r.model_id == model_id and r.tenant_id == tenant_id
        ]
        if not records:
            return ModelPerformanceMetrics(model_id=model_id, tenant_id=tenant_id)

        total = len(records)
        avg_quality = sum(r.quality_score for r in records) / total
        avg_latency = sum(r.latency_ms for r in records) / total
        avg_cost = sum(r.cost for r in records) / total
        success_rate = sum(1 for r in records if r.success) / total

        task_breakdown: dict[str, dict[str, float]] = {}
        for r in records:
            if r.task_type not in task_breakdown:
                task_breakdown[r.task_type] = {"count": 0, "avg_quality": 0.0, "avg_latency": 0.0}
            task_breakdown[r.task_type]["count"] += 1
            task_breakdown[r.task_type]["avg_quality"] += r.quality_score
            task_breakdown[r.task_type]["avg_latency"] += r.latency_ms

        for tt in task_breakdown:
            cnt = task_breakdown[tt]["count"]
            task_breakdown[tt]["avg_quality"] /= cnt
            task_breakdown[tt]["avg_latency"] /= cnt

        return ModelPerformanceMetrics(
            model_id=model_id,
            tenant_id=tenant_id,
            total_evaluations=total,
            avg_quality=round(avg_quality, 3),
            avg_latency_ms=round(avg_latency, 1),
            avg_cost=round(avg_cost, 4),
            success_rate=round(success_rate, 3),
            task_type_breakdown=task_breakdown,
        )

    async def compare_models(
        self, model_ids: list[str], task_type: str, tenant_id: str
    ) -> ModelComparison:
        """Compare multiple models on a specific task type."""
        model_data = []
        for mid in model_ids:
            records = [
                r for r in self._evaluations
                if r.model_id == mid and r.tenant_id == tenant_id and r.task_type == task_type
            ]
            if records:
                avg_q = sum(r.quality_score for r in records) / len(records)
                avg_l = sum(r.latency_ms for r in records) / len(records)
                avg_c = sum(r.cost for r in records) / len(records)
                sr = sum(1 for r in records if r.success) / len(records)
                model_data.append({
                    "model_id": mid,
                    "avg_quality": round(avg_q, 3),
                    "avg_latency_ms": round(avg_l, 1),
                    "avg_cost": round(avg_c, 4),
                    "success_rate": round(sr, 3),
                    "evaluations": len(records),
                })

        model_data.sort(key=lambda x: x["avg_quality"], reverse=True)
        recommendation = model_data[0]["model_id"] if model_data else "No data"

        return ModelComparison(
            task_type=task_type,
            models=model_data,
            recommendation=recommendation,
        )


__all__ = [
    "ModelComparison",
    "ModelEvaluationRecord",
    "ModelEvaluationTracker",
    "ModelPerformanceMetrics",
]
