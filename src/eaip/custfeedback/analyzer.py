"""Feedback analyzer — submit, analyze, aggregate customer feedback."""

from __future__ import annotations

from datetime import datetime

from eaip.custfeedback.exceptions import FeedbackNotFoundError
from eaip.custfeedback.models import FeedbackAggregate, FeedbackItem


class FeedbackAnalyzer:
    def __init__(self) -> None:
        self._feedback: list[FeedbackItem] = []
        self._aggregates: list[FeedbackAggregate] = []

    async def submit_feedback(self, item: FeedbackItem) -> FeedbackItem:
        self._feedback.append(item)
        return item

    async def analyze_feedback(self, feedback_id: str) -> FeedbackItem:
        for i, item in enumerate(self._feedback):
            if item.id == feedback_id:
                analyzed = item.model_copy(
                    update={
                        "sentiment": "positive"
                        if item.rating >= 4
                        else "negative"
                        if item.rating <= 2
                        else "neutral",
                        "analyzed_at": datetime.now(),
                    }
                )
                self._feedback[i] = analyzed
                return analyzed
        raise FeedbackNotFoundError(f"Feedback {feedback_id} not found")

    async def aggregate(self, aggregate: FeedbackAggregate) -> FeedbackAggregate:
        self._aggregates.append(aggregate)
        return aggregate

    async def get_feedback(self, feedback_id: str) -> FeedbackItem | None:
        for f in self._feedback:
            if f.id == feedback_id:
                return f
        return None

    async def list_feedback(self) -> list[FeedbackItem]:
        return list(self._feedback)

    async def list_aggregates(self) -> list[FeedbackAggregate]:
        return list(self._aggregates)

    async def get_aggregate(self, aggregate_id: str) -> FeedbackAggregate | None:
        for a in self._aggregates:
            if a.id == aggregate_id:
                return a
        return None
