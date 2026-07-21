"""Ranking service — result scoring, normalization, and query-aware reranking."""

from __future__ import annotations

import time
from datetime import UTC

from eaip.logging.context import get_logger
from eaip.search.models import SearchQuery, SearchResultItem


class RankingService:
    """Service for ranking and reranking search results.

    Provides score normalization, configurable weighting by recency,
    relevance, and popularity, and query-aware reranking.
    """

    def __init__(
        self,
        *,
        recency_weight: float = 0.2,
        relevance_weight: float = 0.6,
        popularity_weight: float = 0.2,
    ) -> None:
        self._recency_weight = recency_weight
        self._relevance_weight = relevance_weight
        self._popularity_weight = popularity_weight
        self._log = get_logger("eaip.search.ranking")

    @property
    def recency_weight(self) -> float:
        return self._recency_weight

    @property
    def relevance_weight(self) -> float:
        return self._relevance_weight

    @property
    def popularity_weight(self) -> float:
        return self._popularity_weight

    async def rank(
        self,
        items: list[SearchResultItem],
        query: SearchQuery,
    ) -> list[SearchResultItem]:
        """Rank items by relevance score in descending order.

        Args:
            items: The search result items to rank.
            query: The original search query.

        Returns:
            Items sorted by score descending.
        """
        normalized = await self.normalize_scores(items)
        return sorted(normalized, key=lambda i: i.score, reverse=True)

    async def rerank_with_query(
        self,
        items: list[SearchResultItem],
        query: SearchQuery,
    ) -> list[SearchResultItem]:
        """Query-aware reranking with configurable weights.

        Combines recency, relevance (BM25/vector score), and popularity
        into a composite score.

        Args:
            items: The search result items to rerank.
            query: The original search query.

        Returns:
            Reranked items in descending score order.
        """
        if not items:
            return items

        reranked: list[SearchResultItem] = []
        for item in items:
            recency = self._compute_recency_score(item)
            relevance = item.score
            popularity = self._compute_popularity_score(item)

            composite = (
                self._recency_weight * recency
                + self._relevance_weight * relevance
                + self._popularity_weight * popularity
            )

            meta = dict(item.metadata)
            meta["score_recency"] = round(recency, 4)
            meta["score_relevance"] = round(relevance, 4)
            meta["score_popularity"] = round(popularity, 4)
            meta["score_composite"] = round(composite, 4)

            reranked.append(
                SearchResultItem(
                    id=item.id,
                    collection=item.collection,
                    content=item.content,
                    score=composite,
                    title=item.title,
                    source=item.source,
                    metadata=meta,
                    highlights=item.highlights,
                )
            )

        reranked.sort(key=lambda i: i.score, reverse=True)
        return reranked

    async def normalize_scores(
        self,
        items: list[SearchResultItem],
    ) -> list[SearchResultItem]:
        """Normalize scores across items to [0, 1] range.

        Args:
            items: The search result items to normalize.

        Returns:
            Items with scores normalized to [0, 1].
        """
        if not items:
            return items

        min_score = min(i.score for i in items)
        max_score = max(i.score for i in items)
        score_range = max_score - min_score

        if score_range < 1e-10:
            for idx, item in enumerate(items):
                items = self._replace_item(
                    items,
                    idx,
                    1.0 - (idx / max(len(items) - 1, 1)),
                )
        else:
            for idx, item in enumerate(items):
                normalized = (item.score - min_score) / score_range
                items = self._replace_item(items, idx, normalized)

        return items

    @staticmethod
    def _compute_recency_score(item: SearchResultItem) -> float:
        meta = item.metadata
        from datetime import datetime  # noqa: PLC0415

        created_str = meta.get("created_at") or meta.get("timestamp") or ""
        if not created_str:
            return 0.5
        try:
            if isinstance(created_str, (int, float)):
                created_ts = float(created_str)
            else:
                created_dt = datetime.fromisoformat(str(created_str))
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=UTC)
                created_ts = created_dt.timestamp()
            now = time.time()
            age_hours = (now - created_ts) / 3600
            return max(0.0, min(1.0, 1.0 - (age_hours / 8760)))
        except (ValueError, TypeError, OSError):
            return 0.5

    @staticmethod
    def _compute_popularity_score(item: SearchResultItem) -> float:
        meta = item.metadata
        access_count = meta.get("access_count", 0)
        version = meta.get("version", 1)
        if isinstance(access_count, (int, float)):
            return min(1.0, float(access_count) / 100.0)
        if isinstance(version, (int, float)):
            return min(1.0, float(version) / 10.0)
        return 0.5

    @staticmethod
    def _replace_item(
        items: list[SearchResultItem],
        idx: int,
        new_score: float,
    ) -> list[SearchResultItem]:
        item = items[idx]
        items[idx] = SearchResultItem(
            id=item.id,
            collection=item.collection,
            content=item.content,
            score=new_score,
            title=item.title,
            source=item.source,
            metadata=item.metadata,
            highlights=item.highlights,
        )
        return items


__all__ = ["RankingService"]
