"""In-memory persistence store with tenant isolation for learning data."""

from __future__ import annotations

from eaip.learning.models import AdaptationProposal, FeedbackRecord, LearningRecord, Lesson


class LearningStore:
    """Tenant-isolated in-memory store for all learning entities."""

    def __init__(self) -> None:
        self._learning_records: dict[str, LearningRecord] = {}
        self._lessons: dict[str, Lesson] = {}
        self._adaptations: dict[str, AdaptationProposal] = {}
        self._feedback: dict[str, FeedbackRecord] = {}

    def _lr_key(self, tenant_id: str, record_id: str) -> str:
        return f"{tenant_id}:{record_id}"

    def _lesson_key(self, tenant_id: str, lesson_id: str) -> str:
        return f"{tenant_id}:{lesson_id}"

    def _adapt_key(self, tenant_id: str, adapt_id: str) -> str:
        return f"{tenant_id}:{adapt_id}"

    def _fb_key(self, tenant_id: str, fb_id: str) -> str:
        return f"{tenant_id}:{fb_id}"

    # ── Learning Records ────────────────────────────────────────

    def put_learning_record(self, record: LearningRecord) -> None:
        self._learning_records[self._lr_key(record.tenant_id, record.id)] = record

    def get_learning_record(self, tenant_id: str, record_id: str) -> LearningRecord | None:
        return self._learning_records.get(self._lr_key(tenant_id, record_id))

    def list_learning_records(
        self,
        tenant_id: str,
        source_type: str | None = None,
    ) -> list[LearningRecord]:
        results = [
            r
            for k, r in self._learning_records.items()
            if k.startswith(f"{tenant_id}:")
            and (source_type is None or r.source_type == source_type)
        ]
        return sorted(results, key=lambda r: r.created_at, reverse=True)

    # ── Lessons ─────────────────────────────────────────────────

    def put_lesson(self, lesson: Lesson) -> None:
        self._lessons[self._lesson_key(lesson.tenant_id, lesson.id)] = lesson

    def get_lesson(self, tenant_id: str, lesson_id: str) -> Lesson | None:
        return self._lessons.get(self._lesson_key(tenant_id, lesson_id))

    def list_lessons(self, tenant_id: str) -> list[Lesson]:
        results = [l for k, l in self._lessons.items() if k.startswith(f"{tenant_id}:")]
        return sorted(results, key=lambda l: l.created_at if hasattr(l, "created_at") else "", reverse=True)

    # ── Adaptation Proposals ────────────────────────────────────

    def put_adaptation(self, adaptation: AdaptationProposal) -> None:
        self._adaptations[self._adapt_key(adaptation.tenant_id, adaptation.id)] = adaptation

    def get_adaptation(self, tenant_id: str, adapt_id: str) -> AdaptationProposal | None:
        return self._adaptations.get(self._adapt_key(tenant_id, adapt_id))

    def list_adaptations(self, tenant_id: str) -> list[AdaptationProposal]:
        return [a for k, a in self._adaptations.items() if k.startswith(f"{tenant_id}:")]

    # ── Feedback Records ────────────────────────────────────────

    def put_feedback(self, record: FeedbackRecord) -> None:
        self._feedback[self._fb_key(record.tenant_id, record.id)] = record

    def get_feedback(self, tenant_id: str, fb_id: str) -> FeedbackRecord | None:
        return self._feedback.get(self._fb_key(tenant_id, fb_id))

    def list_feedback(self, tenant_id: str) -> list[FeedbackRecord]:
        return [f for k, f in self._feedback.items() if k.startswith(f"{tenant_id}:")]


__all__ = ["LearningStore"]
