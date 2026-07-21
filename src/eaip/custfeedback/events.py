"""Domain events for the customer feedback analyzer."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class FeedbackSubmitted(DomainEvent):
    event_type: ClassVar[str] = "eaip.custfeedback.submitted"

    feedback_id: str
    customer_id: str
    source: str
    rating: int
    category: str


class FeedbackAnalyzed(DomainEvent):
    event_type: ClassVar[str] = "eaip.custfeedback.analyzed"

    feedback_id: str
    sentiment: str
    rating: int
    category: str


class FeedbackAggregated(DomainEvent):
    event_type: ClassVar[str] = "eaip.custfeedback.aggregated"

    aggregate_id: str
    period: str
    category: str
    avg_rating: float
    count: int
    sentiment_distribution: dict[str, int] = Field(default_factory=dict)
