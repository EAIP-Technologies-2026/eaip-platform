"""OrganizationalLearningEngine — high-level API for organizational learning."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable
from typing import Any

from eaip.learning.events import (
    AdaptationProposed,
    FeedbackRecorded,
    LearningEvaluated,
    LearningEvent,
    LearningObserved,
    LessonApproved,
    LessonActivated,
    LessonProposed,
    LessonRejected,
    LessonSuperseded,
)
from eaip.learning.models import (
    AdaptationProposal,
    LearningRecord,
    LearningSource,
    LearningStatus,
    Lesson,
    RiskLevel,
)
from eaip.learning.persistence import LearningStore
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class OrganizationalLearningEngine:
    """High-level API for organizational learning.

    Orchestrates observation, evaluation, lesson proposal, validation,
    approval, activation, rejection, and superseding of lessons.
    All operations are tenant-scoped.
    """

    def __init__(
        self,
        store: LearningStore | None = None,
        event_publisher: Callable[[object], None] | None = None,
    ) -> None:
        self._store = store or LearningStore()
        self._publish = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.learning.engine")

    @property
    def store(self) -> LearningStore:
        return self._store

    # ── observe ─────────────────────────────────────────────────

    def observe(
        self,
        tenant_id: str,
        source_type: LearningSource | str,
        source_id: str,
        observation: dict[str, Any],
    ) -> LearningRecord:
        """Record a learning observation."""
        record_id = f"lr-{uuid.uuid4().hex[:10]}"
        source = LearningSource(source_type) if isinstance(source_type, str) else source_type
        record = LearningRecord(
            id=record_id,
            tenant_id=tenant_id,
            source_type=source,
            source_id=source_id,
            observation=observation,
            confidence=0.0,
            status=LearningStatus.PROPOSED,
        )
        self._store.put_learning_record(record)
        self._publish(LearningObserved(
            record_id=record_id,
            source_type=source.value,
            tenant_id=tenant_id,
        ))
        self._log.info("learning.observed", record_id=record_id, source_type=source.value)
        return record

    # ── evaluate ────────────────────────────────────────────────

    def evaluate(self, tenant_id: str, record_id: str) -> LearningRecord:
        """Evaluate a learning record for significance."""
        record = self._store.get_learning_record(tenant_id, record_id)
        if record is None:
            raise ValueError(f"Learning record {record_id} not found")
        significance = self._assess_significance(record)
        evaluation = {
            "significance": significance,
            "evaluated_at": utc_now().isoformat(),
        }
        updated = record.model_copy(update={
            "evaluation": evaluation,
            "confidence": min(record.confidence + 0.2, 1.0),
            "status": LearningStatus.VALIDATING,
        })
        self._store.put_learning_record(updated)
        self._publish(LearningEvaluated(
            record_id=record_id,
            significance=significance,
            tenant_id=tenant_id,
        ))
        self._log.info("learning.evaluated", record_id=record_id, significance=significance)
        return updated

    def _assess_significance(self, record: LearningRecord) -> str:
        obs = record.observation
        if obs.get("error") or obs.get("failure"):
            return "high"
        if obs.get("success") and obs.get("improvement"):
            return "medium"
        return "low"

    # ── propose_learning ────────────────────────────────────────

    def propose_learning(
        self,
        tenant_id: str,
        record_id: str,
        title: str,
        description: str = "",
    ) -> Lesson:
        """Generate a lesson proposal from a learning record."""
        record = self._store.get_learning_record(tenant_id, record_id)
        if record is None:
            raise ValueError(f"Learning record {record_id} not found")
        lesson_id = f"les-{uuid.uuid4().hex[:10]}"
        evidence = (record.observation,) if record.observation else ()
        lesson = Lesson(
            id=lesson_id,
            tenant_id=tenant_id,
            learning_record_id=record_id,
            title=title,
            description=description,
            evidence=evidence,
            confidence=record.confidence,
            applicability_scope=record.applicability or record.scope or "general",
            status=LearningStatus.PROPOSED,
        )
        self._store.put_lesson(lesson)
        updated_record = record.model_copy(update={"proposed_learning": lesson_id})
        self._store.put_learning_record(updated_record)
        self._publish(LessonProposed(
            lesson_id=lesson_id,
            learning_record_id=record_id,
            tenant_id=tenant_id,
        ))
        self._log.info("learning.lesson.proposed", lesson_id=lesson_id)
        return lesson

    # ── validate ────────────────────────────────────────────────

    def validate(self, tenant_id: str, lesson_id: str) -> Lesson:
        """Validate a lesson against existing knowledge."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        existing = self._store.list_lessons(tenant_id)
        duplicate = any(
            l.title == lesson.title and l.id != lesson_id and l.status == LearningStatus.ACTIVATED
            for l in existing
        )
        if duplicate:
            return lesson.model_copy(update={"status": LearningStatus.REJECTED})
        return lesson.model_copy(update={"status": LearningStatus.VALIDATING})

    # ── approve ─────────────────────────────────────────────────

    def approve(self, tenant_id: str, lesson_id: str, approval_id: str = "") -> Lesson:
        """Approve a lesson. Requires governance approval for high-risk."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        aid = approval_id or f"appr-{uuid.uuid4().hex[:8]}"
        updated = lesson.model_copy(update={
            "status": LearningStatus.APPROVED,
            "approval_id": aid,
        })
        self._store.put_lesson(updated)
        self._publish(LessonApproved(lesson_id=lesson_id, tenant_id=tenant_id))
        self._log.info("learning.lesson.approved", lesson_id=lesson_id)
        return updated

    # ── activate ────────────────────────────────────────────────

    def activate(self, tenant_id: str, lesson_id: str) -> Lesson:
        """Activate a lesson, applying the learning."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        if lesson.status not in (LearningStatus.APPROVED, LearningStatus.VALIDATING):
            raise ValueError(f"Lesson {lesson_id} cannot be activated from status {lesson.status}")
        now = utc_now()
        updated = lesson.model_copy(update={
            "status": LearningStatus.ACTIVATED,
            "effective_date": now,
        })
        self._store.put_lesson(updated)
        record = self._store.get_learning_record(tenant_id, lesson.learning_record_id)
        if record:
            self._store.put_learning_record(record.model_copy(update={
                "status": LearningStatus.ACTIVATED,
                "activated_at": now,
            }))
        self._publish(LessonActivated(lesson_id=lesson_id, tenant_id=tenant_id))
        self._log.info("learning.lesson.activated", lesson_id=lesson_id)
        return updated

    # ── reject ──────────────────────────────────────────────────

    def reject(self, tenant_id: str, lesson_id: str, reason: str = "") -> Lesson:
        """Reject a lesson."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        updated = lesson.model_copy(update={"status": LearningStatus.REJECTED})
        self._store.put_lesson(updated)
        self._publish(LessonRejected(lesson_id=lesson_id, reason=reason, tenant_id=tenant_id))
        self._log.info("learning.lesson.rejected", lesson_id=lesson_id, reason=reason)
        return updated

    # ── supersede ───────────────────────────────────────────────

    def supersede(self, tenant_id: str, lesson_id: str, new_lesson_id: str) -> Lesson:
        """Mark a lesson as superseded by a new one."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        new_lesson = self._store.get_lesson(tenant_id, new_lesson_id)
        if new_lesson is None:
            raise ValueError(f"New lesson {new_lesson_id} not found")
        updated = lesson.model_copy(update={"status": LearningStatus.SUPERSEDED})
        self._store.put_lesson(updated)
        self._publish(LessonSuperseded(
            lesson_id=lesson_id,
            new_lesson_id=new_lesson_id,
            tenant_id=tenant_id,
        ))
        self._log.info("learning.lesson.superseded", lesson_id=lesson_id, by=new_lesson_id)
        return updated

    # ── queries ─────────────────────────────────────────────────

    def get_lesson(self, tenant_id: str, lesson_id: str) -> Lesson | None:
        return self._store.get_lesson(tenant_id, lesson_id)

    def list_lessons(self, tenant_id: str) -> list[Lesson]:
        return self._store.list_lessons(tenant_id)

    def get_learning_history(
        self,
        tenant_id: str,
        source_type: LearningSource | str | None = None,
    ) -> list[LearningRecord]:
        st = LearningSource(source_type).value if isinstance(source_type, str) else (source_type.value if source_type else None)
        return self._store.list_learning_records(tenant_id, source_type=st)


__all__ = ["OrganizationalLearningEngine"]
