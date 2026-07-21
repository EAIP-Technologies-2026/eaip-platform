"""Tests for search strategies — semantic, keyword, hybrid, reranking."""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.models import (
    DocumentChunk,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    SourceAttribution,
)
from eaip.knowledge.search_strategies import (
    CrossEncoderReranker,
    HybridSearchStrategy,
    KeywordSearchStrategy,
    RerankingStrategy,
    SearchStrategy,
    SemanticSearchStrategy,
    SimpleReranker,
)


class _MockVectorStore:
    def __init__(self) -> None:
        self._results: list[dict[str, object]] = []

    def set_results(self, results: list[dict[str, object]]) -> None:
        self._results = results

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        pass

    async def upsert_points(self, collection: str, chunks: list[DocumentChunk]) -> None:
        pass

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        pass

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict[str, object]]:
        return self._results

    async def delete_collection(self, name: str) -> None:
        pass

    async def list_collections(self) -> list[str]:
        return []

    async def collection_info(self, name: str) -> dict[str, object]:
        return {}


class TestSemanticSearchStrategy:
    @pytest.mark.asyncio
    async def test_search_returns_result(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.9,
                    "payload": {"document_id": "d1", "content": "semantic", "chunk_index": 0},
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        strategy = SemanticSearchStrategy(store, embedding)

        config = RetrievalQuery(query="test", top_k=5)
        result = await strategy.search("test", "default", config)
        assert result.total_results == 1
        assert result.chunks[0].content == "semantic"

    @pytest.mark.asyncio
    async def test_search_empty(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        strategy = SemanticSearchStrategy(store, embedding)

        config = RetrievalQuery(query="test", top_k=5)
        result = await strategy.search("test", "default", config)
        assert result.total_results == 0


class TestKeywordSearchStrategy:
    @pytest.mark.asyncio
    async def test_search_returns_empty_result(self) -> None:
        strategy = KeywordSearchStrategy()
        config = RetrievalQuery(query="test", top_k=5)
        result = await strategy.search("test", "default", config)
        assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_score_keyword(self) -> None:
        strategy = KeywordSearchStrategy()
        chunks = [
            RetrievedChunk(
                chunk_id="c1",
                document_id="d1",
                collection="default",
                content="The cat sat on the mat",
                score=0.5,
                attribution=SourceAttribution(document_id="d1", collection="default"),
            ),
            RetrievedChunk(
                chunk_id="c2",
                document_id="d2",
                collection="default",
                content="The dog ran in the park",
                score=0.4,
                attribution=SourceAttribution(document_id="d2", collection="default"),
            ),
        ]

        scored = await strategy.score_keyword(chunks, "cat mat")
        assert len(scored) == 2
        assert scored[0].chunk_id == "c1"


class TestHybridSearchStrategy:
    @pytest.mark.asyncio
    async def test_hybrid_search(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.9,
                    "payload": {"document_id": "d1", "content": "semantic match", "chunk_index": 0},
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        semantic = SemanticSearchStrategy(store, embedding)
        keyword = KeywordSearchStrategy()
        strategy = HybridSearchStrategy(semantic, keyword)

        config = RetrievalQuery(query="test", top_k=5, alpha=0.7)
        result = await strategy.search("test", "default", config)
        assert result.total_results == 1


class TestSimpleReranker:
    @pytest.mark.asyncio
    async def test_rerank_orders_by_score(self) -> None:
        reranker = SimpleReranker()
        chunks = [
            RetrievedChunk(
                chunk_id="c1",
                document_id="d1",
                collection="default",
                content="low",
                score=0.3,
                attribution=SourceAttribution(document_id="d1", collection="default"),
            ),
            RetrievedChunk(
                chunk_id="c2",
                document_id="d2",
                collection="default",
                content="high",
                score=0.9,
                attribution=SourceAttribution(document_id="d2", collection="default"),
            ),
        ]

        reranked = await reranker.rerank(chunks, "test")
        assert reranked[0].score == 0.9
        assert reranked[1].score == 0.3

    @pytest.mark.asyncio
    async def test_rerank_empty(self) -> None:
        reranker = SimpleReranker()
        result = await reranker.rerank([], "test")
        assert result == []


class TestCrossEncoderReranker:
    @pytest.mark.asyncio
    async def test_rerank_preserves_order(self) -> None:
        reranker = CrossEncoderReranker()
        chunks = [
            RetrievedChunk(
                chunk_id="c1",
                document_id="d1",
                collection="default",
                content="first",
                score=0.9,
                attribution=SourceAttribution(document_id="d1", collection="default"),
            ),
            RetrievedChunk(
                chunk_id="c2",
                document_id="d2",
                collection="default",
                content="second",
                score=0.7,
                attribution=SourceAttribution(document_id="d2", collection="default"),
            ),
        ]

        reranked = await reranker.rerank(chunks, "test")
        assert len(reranked) == 2

    @pytest.mark.asyncio
    async def test_rerank_empty(self) -> None:
        reranker = CrossEncoderReranker()
        result = await reranker.rerank([], "test")
        assert result == []


class TestSearchStrategyProtocol:
    def test_protocol_runtime_checkable(self) -> None:
        class ValidStrategy:
            async def search(
                self, query: str, collection: str, config: RetrievalQuery
            ) -> RetrievalResult:
                return RetrievalResult(query=query, collection=collection, total_results=0)

        assert isinstance(ValidStrategy(), SearchStrategy)

    def test_reranking_protocol_runtime_checkable(self) -> None:
        class ValidReranker:
            async def rerank(
                self, results: list[RetrievedChunk], query: str
            ) -> list[RetrievedChunk]:
                return results

        assert isinstance(ValidReranker(), RerankingStrategy)
