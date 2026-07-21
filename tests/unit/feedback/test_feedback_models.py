"""Tests for :mod:`eaip.feedback.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.feedback.models import FeedbackCategory, FeedbackConfig, FeedbackItem, FeedbackRating


class TestFeedbackItem:
    """Tests for :class:`eaip.feedback.models.FeedbackItem`."""

    def test_create_minimal(self) -> None:
        """Test creating an item with required fields."""
        item = FeedbackItem(
            id="f1",
            user_id="u1",
            rating=FeedbackRating.POSITIVE,
            category=FeedbackCategory.BUG,
        )
        assert item.acknowledged is False
        assert item.escalated is False

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        item = FeedbackItem(
            id="f1",
            user_id="u1",
            rating=FeedbackRating.POSITIVE,
            category=FeedbackCategory.BUG,
        )
        with pytest.raises(ValidationError):
            item.rating = FeedbackRating.NEGATIVE


class TestFeedbackConfig:
    """Tests for :class:`eaip.feedback.models.FeedbackConfig`."""

    def test_defaults(self) -> None:
        """Test default configuration values."""
        c = FeedbackConfig()
        assert c.enabled is True
        assert c.max_message_length == 2000
        assert c.require_category is True

    def test_custom(self) -> None:
        """Test creating a config with custom values."""
        c = FeedbackConfig(enabled=False, max_message_length=500, require_category=False)
        assert c.enabled is False
        assert c.max_message_length == 500

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        c = FeedbackConfig()
        with pytest.raises(ValidationError):
            c.enabled = False


class TestFeedbackRating:
    """Tests for :class:`eaip.feedback.models.FeedbackRating`."""

    def test_values(self) -> None:
        """Test the enum values."""
        assert FeedbackRating.POSITIVE.value == "positive"
        assert FeedbackRating.NEUTRAL.value == "neutral"
        assert FeedbackRating.NEGATIVE.value == "negative"


class TestFeedbackCategory:
    """Tests for :class:`eaip.feedback.models.FeedbackCategory`."""

    def test_values(self) -> None:
        """Test the enum values."""
        assert FeedbackCategory.BUG.value == "bug"
        assert FeedbackCategory.FEATURE.value == "feature"
        assert FeedbackCategory.PERFORMANCE.value == "performance"
        assert FeedbackCategory.UX.value == "ux"
        assert FeedbackCategory.OTHER.value == "other"


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        FeedbackItem(
            id="f1",
            user_id="u1",
            rating=FeedbackRating.POSITIVE,
            category=FeedbackCategory.BUG,
            unknown="val",
        )
