"""FeedbackLoop — record outcomes for predictions, decisions, workflows, agents."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.learning.events import FeedbackRecorded
from eaip.learning.models import FeedbackRecord, LearningSource
from eaip.learning.persistence import LearningStore
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class FeedbackLoop:
    """Records actual outcomes against predictions, decisions, workflows, and agent performance.

    Generates learning records when outcomes diverge from expectations.
    """

    def __init__(
        self,
        store: LearningStore,
        event_publisher: object | None = None,
        learning_engine: object | None = None,
    ) -> None:
        self._store = store
        self._publish = event_publisher or (lambda _: None)
        self._engine = learning_engine
        self._log = get_logger("eaip.learning.feedback")

    def record_prediction_outcome(
        self,
        tenant_id: str,
        prediction_id: str,
        actual_outcome: dict[str, Any],
        predicted_outcome: dict[str, Any] | None = None,
    ) -> FeedbackRecord:
        """Record the actual outcome for a prediction and calculate error."""
        error = self._calculate_prediction_error(predicted_outcome or {}, actual_outcome)
        quality = max(0.0, 1.0 - error)
        fb_id = f"fb-{uuid.uuid4().hex[:10]}"
        record = FeedbackRecord(
            id=fb_id,
            tenant_id=tenant_id,
            source_type=LearningSource.PREDICTION,
            source_id=prediction_id,
            actual_outcome=actual_outcome,
            error=error,
            quality_score=quality,
        )
        self._store.put_feedback(record)
        self._publish(FeedbackRecorded(
            feedback_id=fb_id,
            source_type=LearningSource.PREDICTION.value,
            source_id=prediction_id,
            tenant_id=tenant_id,
        ))
        self._log.info("feedback.prediction", feedback_id=fb_id, error=error, quality=quality)
        return record

    def record_decision_outcome(
        self,
        tenant_id: str,
        decision_id: str,
        actual_outcome: dict[str, Any],
    ) -> FeedbackRecord:
        """Record the actual outcome for a decision."""
        quality = self._assess_decision_quality(actual_outcome)
        fb_id = f"fb-{uuid.uuid4().hex[:10]}"
        record = FeedbackRecord(
            id=fb_id,
            tenant_id=tenant_id,
            source_type=LearningSource.DECISION,
            source_id=decision_id,
            actual_outcome=actual_outcome,
            error=1.0 - quality,
            quality_score=quality,
        )
        self._store.put_feedback(record)
        self._publish(FeedbackRecorded(
            feedback_id=fb_id,
            source_type=LearningSource.DECISION.value,
            source_id=decision_id,
            tenant_id=tenant_id,
        ))
        self._log.info("feedback.decision", feedback_id=fb_id, quality=quality)
        return record

    def record_workflow_outcome(
        self,
        tenant_id: str,
        workflow_id: str,
        success: bool,
        details: dict[str, Any] | None = None,
    ) -> FeedbackRecord:
        """Record the outcome of a workflow execution."""
        quality = 1.0 if success else 0.0
        fb_id = f"fb-{uuid.uuid4().hex[:10]}"
        record = FeedbackRecord(
            id=fb_id,
            tenant_id=tenant_id,
            source_type=LearningSource.WORKFLOW,
            source_id=workflow_id,
            actual_outcome={"success": success, **(details or {})},
            error=1.0 - quality,
            quality_score=quality,
        )
        self._store.put_feedback(record)
        self._publish(FeedbackRecorded(
            feedback_id=fb_id,
            source_type=LearningSource.WORKFLOW.value,
            source_id=workflow_id,
            tenant_id=tenant_id,
        ))
        self._log.info("feedback.workflow", feedback_id=fb_id, success=success)
        return record

    def record_agent_performance(
        self,
        tenant_id: str,
        agent_id: str,
        metrics: dict[str, Any],
    ) -> FeedbackRecord:
        """Record agent performance metrics."""
        quality = self._compute_agent_quality(metrics)
        fb_id = f"fb-{uuid.uuid4().hex[:10]}"
        record = FeedbackRecord(
            id=fb_id,
            tenant_id=tenant_id,
            source_type=LearningSource.AGENT_PERFORMANCE,
            source_id=agent_id,
            actual_outcome=metrics,
            error=1.0 - quality,
            quality_score=quality,
        )
        self._store.put_feedback(record)
        self._publish(FeedbackRecorded(
            feedback_id=fb_id,
            source_type=LearningSource.AGENT_PERFORMANCE.value,
            source_id=agent_id,
            tenant_id=tenant_id,
        ))
        self._log.info("feedback.agent", feedback_id=fb_id, quality=quality)
        return record

    def get_feedback_summary(self, tenant_id: str) -> dict[str, Any]:
        """Get aggregated feedback summary for a tenant."""
        records = self._store.list_feedback(tenant_id)
        if not records:
            return {"total": 0, "avg_error": 0.0, "avg_quality": 0.0, "by_source": {}}
        by_source: dict[str, list[FeedbackRecord]] = {}
        for r in records:
            by_source.setdefault(r.source_type.value, []).append(r)
        summary: dict[str, Any] = {}
        for src, recs in by_source.items():
            summary[src] = {
                "count": len(recs),
                "avg_error": round(sum(r.error for r in recs) / len(recs), 4),
                "avg_quality": round(sum(r.quality_score for r in recs) / len(recs), 4),
            }
        return {
            "total": len(records),
            "avg_error": round(sum(r.error for r in records) / len(records), 4),
            "avg_quality": round(sum(r.quality_score for r in records) / len(records), 4),
            "by_source": summary,
        }

    # ── helpers ─────────────────────────────────────────────────

    def _calculate_prediction_error(
        self,
        predicted: dict[str, Any],
        actual: dict[str, Any],
    ) -> float:
        if not predicted:
            return 0.5
        mismatches = 0
        total = max(len(predicted), len(actual))
        if total == 0:
            return 0.0
        for k in set(predicted.keys()) | set(actual.keys()):
            pv = predicted.get(k)
            av = actual.get(k)
            if pv != av:
                mismatches += 1
        return round(mismatches / total, 4)

    def _assess_decision_quality(self, outcome: dict[str, Any]) -> float:
        if outcome.get("success"):
            return 0.8
        if outcome.get("partial_success"):
            return 0.5
        return 0.2

    def _compute_agent_quality(self, metrics: dict[str, Any]) -> float:
        success_rate = float(metrics.get("success_rate", 0.5))
        latency_score = min(1.0, float(metrics.get("latency_ms", 5000)) / 10000)
        return round((success_rate + (1.0 - latency_score)) / 2, 4)


__all__ = ["FeedbackLoop"]
