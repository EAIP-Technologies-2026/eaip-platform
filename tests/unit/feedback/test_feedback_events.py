"""Tests for :mod:`eaip.feedback.events`."""

from __future__ import annotations

import pytest

from eaip.feedback.events import FeedbackAcknowledged, FeedbackEscalated, FeedbackSubmitted
from eaip.feedback.models import FeedbackCategory, FeedbackRating


class TestFeedbackSubmitted:
    """Tests for :class:`eaip.feedback.events.FeedbackSubmitted`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = FeedbackSubmitted(
            feedback_id="f1",
            user_id="u1",
            rating=FeedbackRating.POSITIVE,
            category=FeedbackCategory.FEATURE,
        )
        assert e.event_type == "eaip.feedback.feedback.submitted"
        assert e.rating is FeedbackRating.POSITIVE

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = FeedbackSubmitted(
            feedback_id="f1",
            user_id="u1",
            rating=FeedbackRating.POSITIVE,
            category=FeedbackCategory.BUG,
        )
        with pytest.raises(ValueError):
            e.feedback_id = "f2"


class TestFeedbackAcknowledged:
    """Tests for :class:`eaip.feedback.events.FeedbackAcknowledged`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = FeedbackAcknowledged(feedback_id="f1", acknowledged_by="admin")
        assert e.event_type == "eaip.feedback.feedback.acknowledged"
        assert e.acknowledged_by == "admin"


class TestFeedbackEscalated:
    """Tests for :class:`eaip.feedback.events.FeedbackEscalated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = FeedbackEscalated(feedback_id="f1", reason="spam", escalated_to="moderator")
        assert e.event_type == "eaip.feedback.feedback.escalated"
        assert e.reason == "spam"


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        FeedbackSubmitted(
            feedback_id="f1",
            user_id="u1",
            rating=FeedbackRating.POSITIVE,
            category=FeedbackCategory.BUG,
        ).event_type,
        FeedbackAcknowledged(feedback_id="f1", acknowledged_by="a").event_type,
        FeedbackEscalated(feedback_id="f1").event_type,
    ]
    assert len(types) == len(set(types))
