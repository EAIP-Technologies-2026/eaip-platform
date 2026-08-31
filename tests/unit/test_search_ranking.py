from __future__ import annotations

import pytest

from eaip.search.models import SearchQuery, SearchResultItem
from eaip.search.ranking import RankingService


class TestRankingService:
    def test_default_weights(self) -> None:
        svc = RankingService()
        assert svc.relevance_weight == 0.6
        assert svc.recency_weight == 0.2
        assert svc.popularity_weight == 0.2

    def test_custom_weights(self) -> None:
        svc = RankingService(recency_weight=0.1, relevance_weight=0.8, popularity_weight=0.1)
        assert svc.recency_weight == 0.1
        assert svc.relevance_weight == 0.8

    @pytest.mark.asyncio
    async def test_rank_empty(self) -> None:
        svc = RankingService()
        result = await svc.rank([], SearchQuery(query="test"))
        assert result == []

    @pytest.mark.asyncio
    async def test_rank_sorts_by_score_descending(self) -> None:
        svc = RankingService()
        items = [
            SearchResultItem(id="1", collection="c", content="a", score=0.5),
            SearchResultItem(id="2", collection="c", content="b", score=0.9),
            SearchResultItem(id="3", collection="c", content="c", score=0.3),
        ]
        result = await svc.rank(items, SearchQuery(query="test"))
        assert result[0].id == "2"
        assert result[1].id == "1"
        assert result[2].id == "3"

    @pytest.mark.asyncio
    async def test_normalize_scores(self) -> None:
        svc = RankingService()
        items = [
            SearchResultItem(id="1", collection="c", content="a", score=10.0),
            SearchResultItem(id="2", collection="c", content="b", score=20.0),
            SearchResultItem(id="3", collection="c", content="c", score=30.0),
        ]
        result = await svc.normalize_scores(items)
        assert abs(result[0].score - 0.0) < 1e-6
        assert abs(result[1].score - 0.5) < 1e-6
        assert abs(result[2].score - 1.0) < 1e-6

    @pytest.mark.asyncio
    async def test_normalize_scores_uniform(self) -> None:
        svc = RankingService()
        items = [
            SearchResultItem(id="1", collection="c", content="a", score=5.0),
            SearchResultItem(id="2", collection="c", content="b", score=5.0),
        ]
        result = await svc.normalize_scores(items)
        assert result[0].score >= result[1].score

    @pytest.mark.asyncio
    async def test_rerank_with_query(self) -> None:
        svc = RankingService()
        items = [
            SearchResultItem(
                id="1", collection="c", content="a", score=0.8, metadata={"access_count": 50}
            ),
            SearchResultItem(
                id="2", collection="c", content="b", score=0.6, metadata={"access_count": 10}
            ),
        ]
        result = await svc.rerank_with_query(items, SearchQuery(query="test"))
        assert len(result) == 2
        assert "score_composite" in result[0].metadata
        assert "score_relevance" in result[0].metadata

    @pytest.mark.asyncio
    async def test_rerank_empty(self) -> None:
        svc = RankingService()
        result = await svc.rerank_with_query([], SearchQuery(query="test"))
        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_uses_composite_score(self) -> None:
        svc = RankingService(recency_weight=0.0, relevance_weight=1.0, popularity_weight=0.0)
        items = [
            SearchResultItem(id="a", collection="c", content="a", score=0.3),
            SearchResultItem(id="b", collection="c", content="b", score=0.9),
        ]
        result = await svc.rerank_with_query(items, SearchQuery(query="test"))
        assert result[0].id == "b"
        assert result[0].score == pytest.approx(0.9)
