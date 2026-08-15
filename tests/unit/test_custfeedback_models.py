"""Tests for :mod:`eaip.custfeedback.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.custfeedback.models import AnalyzerConfig, FeedbackAggregate, FeedbackItem


class TestFeedbackItem:
    def test_create_minimal(self) -> None:
        f = FeedbackItem(id="f1", customer_id="c1", source="web", rating=5, category="general")
        assert f.id == "f1"
        assert f.rating == 5
        assert f.category == "general"
        assert f.sentiment is None
        assert f.comment is None

    def test_create_full(self) -> None:
        f = FeedbackItem(
            id="f2",
            customer_id="c1",
            source="email",
            rating=3,
            category="billing",
            sentiment="neutral",
            comment="Okay service",
        )
        assert f.sentiment == "neutral"
        assert f.comment == "Okay service"

    def test_frozen(self) -> None:
        f = FeedbackItem(id="f3", customer_id="c1", source="web", rating=4, category="general")
        with pytest.raises(ValidationError):
            f.rating = 5


class TestFeedbackAggregate:
    def test_create_minimal(self) -> None:
        a = FeedbackAggregate(
            id="a1", period="2024-01", category="general", avg_rating=4.5, count=10
        )
        assert a.avg_rating == 4.5
        assert a.count == 10
        assert a.sentiment_distribution == {}

    def test_with_distribution(self) -> None:
        a = FeedbackAggregate(
            id="a2",
            period="2024-01",
            category="support",
            avg_rating=3.2,
            count=25,
            sentiment_distribution={"positive": 10, "neutral": 10, "negative": 5},
        )
        assert a.sentiment_distribution["positive"] == 10

    def test_frozen(self) -> None:
        a = FeedbackAggregate(
            id="a3", period="2024-01", category="general", avg_rating=4.0, count=5
        )
        with pytest.raises(ValidationError):
            a.count = 10


class TestAnalyzerConfig:
    def test_defaults(self) -> None:
        c = AnalyzerConfig()
        assert c.min_feedback_for_aggregation == 5
        assert c.aggregation_interval_hours == 24
        assert c.enable_sentiment_analysis is True
        assert c.data_retention_days == 365

    def test_custom(self) -> None:
        c = AnalyzerConfig(
            min_feedback_for_aggregation=10,
            aggregation_interval_hours=12,
            enable_sentiment_analysis=False,
        )
        assert c.min_feedback_for_aggregation == 10
        assert c.enable_sentiment_analysis is False

    def test_frozen(self) -> None:
        c = AnalyzerConfig()
        with pytest.raises(ValidationError):
            c.min_feedback_for_aggregation = 20


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        FeedbackItem(
            id="x", customer_id="c1", source="web", rating=5, category="g", unknown="field"
        )
