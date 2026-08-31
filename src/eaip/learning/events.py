"""Learning domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class LearningEvent(DomainEvent):
    """Base event for all Learning Engine events."""

    event_type: ClassVar[str] = "eaip.learning.event"


class LearningObserved(LearningEvent):
    """Published when a learning observation is recorded."""

    event_type: ClassVar[str] = "eaip.learning.observed"
    record_id: str
    source_type: str
    tenant_id: str


class LearningEvaluated(LearningEvent):
    """Published when a learning record is evaluated."""

    event_type: ClassVar[str] = "eaip.learning.evaluated"
    record_id: str
    significance: str = ""
    tenant_id: str


class LessonProposed(LearningEvent):
    """Published when a lesson is proposed."""

    event_type: ClassVar[str] = "eaip.learning.lesson.proposed"
    lesson_id: str
    learning_record_id: str
    tenant_id: str


class LessonApproved(LearningEvent):
    """Published when a lesson is approved."""

    event_type: ClassVar[str] = "eaip.learning.lesson.approved"
    lesson_id: str
    tenant_id: str


class LessonActivated(LearningEvent):
    """Published when a lesson is activated."""

    event_type: ClassVar[str] = "eaip.learning.lesson.activated"
    lesson_id: str
    tenant_id: str


class LessonRejected(LearningEvent):
    """Published when a lesson is rejected."""

    event_type: ClassVar[str] = "eaip.learning.lesson.rejected"
    lesson_id: str
    reason: str = ""
    tenant_id: str


class LessonSuperseded(LearningEvent):
    """Published when a lesson is superseded."""

    event_type: ClassVar[str] = "eaip.learning.lesson.superseded"
    lesson_id: str
    new_lesson_id: str
    tenant_id: str


class AdaptationProposed(LearningEvent):
    """Published when an adaptation proposal is created."""

    event_type: ClassVar[str] = "eaip.learning.adaptation.proposed"
    adaptation_id: str
    lesson_id: str
    target_type: str
    risk_level: str
    tenant_id: str


class FeedbackRecorded(LearningEvent):
    """Published when a feedback record is created."""

    event_type: ClassVar[str] = "eaip.learning.feedback.recorded"
    feedback_id: str
    source_type: str
    source_id: str
    tenant_id: str


__all__ = [
    "AdaptationProposed",
    "FeedbackRecorded",
    "LearningEvent",
    "LearningEvaluated",
    "LearningObserved",
    "LessonApproved",
    "LessonActivated",
    "LessonProposed",
    "LessonRejected",
    "LessonSuperseded",
]
