"""Tests for :mod:`eaip.custfeedback.events`."""

from __future__ import annotations

import pytest

from eaip.custfeedback.events import FeedbackAggregated, FeedbackAnalyzed, FeedbackSubmitted


class TestFeedbackSubmitted:
    def test_create(self) -> None:
        e = FeedbackSubmitted(
            feedback_id="f1", customer_id="c1", source="web", rating=5, category="general"
        )
        assert e.event_type == "eaip.custfeedback.submitted"
        assert e.feedback_id == "f1"

    def test_frozen(self) -> None:
        e = FeedbackSubmitted(
            feedback_id="f1", customer_id="c1", source="web", rating=5, category="general"
        )
        with pytest.raises(ValueError):
            e.rating = 3


class TestFeedbackAnalyzed:
    def test_create(self) -> None:
        e = FeedbackAnalyzed(feedback_id="f1", sentiment="positive", rating=5, category="general")
        assert e.event_type == "eaip.custfeedback.analyzed"


class TestFeedbackAggregated:
    def test_create(self) -> None:
        e = FeedbackAggregated(
            aggregate_id="a1",
            period="2024-01",
            category="general",
            avg_rating=4.5,
            count=10,
            sentiment_distribution={"positive": 8, "neutral": 1, "negative": 1},
        )
        assert e.event_type == "eaip.custfeedback.aggregated"
        assert e.avg_rating == 4.5
