"""Domain events for feedback collection."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.feedback.models import FeedbackCategory, FeedbackRating


class FeedbackSubmitted(DomainEvent):
    """Emitted when feedback is submitted."""

    event_type: ClassVar[str] = "eaip.feedback.feedback.submitted"

    feedback_id: str
    user_id: str
    rating: FeedbackRating
    category: FeedbackCategory


class FeedbackAcknowledged(DomainEvent):
    """Emitted when feedback is acknowledged."""

    event_type: ClassVar[str] = "eaip.feedback.feedback.acknowledged"

    feedback_id: str
    acknowledged_by: str


class FeedbackEscalated(DomainEvent):
    """Emitted when feedback is escalated."""

    event_type: ClassVar[str] = "eaip.feedback.feedback.escalated"

    feedback_id: str
    reason: str = Field(default="")
    escalated_to: str = Field(default="")


__all__ = [
    "FeedbackAcknowledged",
    "FeedbackEscalated",
    "FeedbackSubmitted",
]
