"""Tests for :mod:`eaip.custfeedback.analyzer`."""

from __future__ import annotations

import pytest

from eaip.custfeedback.analyzer import FeedbackAnalyzer
from eaip.custfeedback.exceptions import FeedbackNotFoundError
from eaip.custfeedback.models import FeedbackAggregate, FeedbackItem


@pytest.fixture
def analyzer() -> FeedbackAnalyzer:
    return FeedbackAnalyzer()


class TestFeedbackAnalyzer:
    @pytest.mark.asyncio
    async def test_submit_feedback(self, analyzer: FeedbackAnalyzer) -> None:
        f = FeedbackItem(id="f1", customer_id="c1", source="web", rating=5, category="general")
        result = await analyzer.submit_feedback(f)
        assert result.id == "f1"

    @pytest.mark.asyncio
    async def test_list_feedback_empty(self, analyzer: FeedbackAnalyzer) -> None:
        assert await analyzer.list_feedback() == []

    @pytest.mark.asyncio
    async def test_get_feedback_found(self, analyzer: FeedbackAnalyzer) -> None:
        f = FeedbackItem(id="f1", customer_id="c1", source="web", rating=5, category="general")
        await analyzer.submit_feedback(f)
        found = await analyzer.get_feedback("f1")
        assert found is not None
        assert found.rating == 5

    @pytest.mark.asyncio
    async def test_get_feedback_not_found(self, analyzer: FeedbackAnalyzer) -> None:
        found = await analyzer.get_feedback("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_analyze_feedback_positive(self, analyzer: FeedbackAnalyzer) -> None:
        f = FeedbackItem(id="f1", customer_id="c1", source="web", rating=5, category="general")
        await analyzer.submit_feedback(f)
        analyzed = await analyzer.analyze_feedback("f1")
        assert analyzed.sentiment == "positive"
        assert analyzed.analyzed_at is not None

    @pytest.mark.asyncio
    async def test_analyze_feedback_negative(self, analyzer: FeedbackAnalyzer) -> None:
        f = FeedbackItem(id="f1", customer_id="c1", source="web", rating=1, category="general")
        await analyzer.submit_feedback(f)
        analyzed = await analyzer.analyze_feedback("f1")
        assert analyzed.sentiment == "negative"

    @pytest.mark.asyncio
    async def test_analyze_feedback_neutral(self, analyzer: FeedbackAnalyzer) -> None:
        f = FeedbackItem(id="f1", customer_id="c1", source="web", rating=3, category="general")
        await analyzer.submit_feedback(f)
        analyzed = await analyzer.analyze_feedback("f1")
        assert analyzed.sentiment == "neutral"

    @pytest.mark.asyncio
    async def test_analyze_not_found(self, analyzer: FeedbackAnalyzer) -> None:
        with pytest.raises(FeedbackNotFoundError):
            await analyzer.analyze_feedback("nonexistent")

    @pytest.mark.asyncio
    async def test_aggregate(self, analyzer: FeedbackAnalyzer) -> None:
        a = FeedbackAggregate(
            id="a1", period="2024-01", category="general", avg_rating=4.5, count=10
        )
        result = await analyzer.aggregate(a)
        assert result.id == "a1"

    @pytest.mark.asyncio
    async def test_get_aggregate_found(self, analyzer: FeedbackAnalyzer) -> None:
        a = FeedbackAggregate(
            id="a1", period="2024-01", category="general", avg_rating=4.5, count=10
        )
        await analyzer.aggregate(a)
        found = await analyzer.get_aggregate("a1")
        assert found is not None
        assert found.avg_rating == 4.5

    @pytest.mark.asyncio
    async def test_get_aggregate_not_found(self, analyzer: FeedbackAnalyzer) -> None:
        found = await analyzer.get_aggregate("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_aggregates(self, analyzer: FeedbackAnalyzer) -> None:
        a = FeedbackAggregate(
            id="a1", period="2024-01", category="general", avg_rating=4.5, count=10
        )
        await analyzer.aggregate(a)
        aggregates = await analyzer.list_aggregates()
        assert len(aggregates) == 1
