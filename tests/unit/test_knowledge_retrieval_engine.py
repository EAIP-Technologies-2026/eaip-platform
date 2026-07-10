"""Tests for RetrievalEngine — hybrid search, reranking, multi-collection."""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.models import (
    DocumentChunk,
    RetrievalQuery,
    RetrievedChunk,
)
from eaip.knowledge.retrieval_engine import RetrievalEngine


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
        return ["col_a", "col_b"]

    async def collection_info(self, name: str) -> dict[str, object]:
        return {}


class TestRetrievalEngine:
    @pytest.mark.asyncio
    async def test_search_empty(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search("hello")
        assert result.total_results == 0
        assert result.query == "hello"
        assert result.chunks == ()

    @pytest.mark.asyncio
    async def test_search_with_results(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {
                "id": "chunk1",
                "score": 0.95,
                "payload": {
                    "document_id": "doc1",
                    "content": "Test content",
                    "chunk_index": 0,
                    "source": "test.txt",
                    "title": "Test Doc",
                    "collection": "default",
                },
            },
        ])
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search("test query")
        assert result.total_results == 1
        assert result.chunks[0].content == "Test content"
        assert result.chunks[0].score >= 0.0

    @pytest.mark.asyncio
    async def test_search_semantic(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.9, "payload": {"document_id": "d1", "content": "Semantic hit", "chunk_index": 0}},
        ])
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search_semantic("test query")
        assert result.total_results == 1

    @pytest.mark.asyncio
    async def test_search_keyword(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search_keyword("test")
        assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_search_multi(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.9, "payload": {"document_id": "d1", "content": "A", "chunk_index": 0}},
        ])
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search_multi("test", ["a", "b"])
        assert result.total_results == 1

    @pytest.mark.asyncio
    async def test_search_with_reranking(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.7, "payload": {"document_id": "d1", "content": "Lower", "chunk_index": 0}},
            {"id": "c2", "score": 0.9, "payload": {"document_id": "d2", "content": "Higher", "chunk_index": 1}},
        ])
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search("test", enable_reranking=True)
        assert result.total_results == 2
        assert result.chunks[0].score >= result.chunks[-1].score

    @pytest.mark.asyncio
    async def test_search_with_score_threshold(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.3, "payload": {"document_id": "d1", "content": "Low", "chunk_index": 0}},
            {"id": "c2", "score": 0.8, "payload": {"document_id": "d2", "content": "High", "chunk_index": 1}},
        ])
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding, default_score_threshold=0.5)

        result = await engine.search("test", score_threshold=0.5)
        assert result.total_results == 1

    @pytest.mark.asyncio
    async def test_context_assembly(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.9, "payload": {"document_id": "d1", "content": "First", "chunk_index": 0}},
            {"id": "c2", "score": 0.8, "payload": {"document_id": "d2", "content": "Second", "chunk_index": 1}},
        ])
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search("test")
        assert result.context is not None
        assert "First" in result.context.context
        assert result.context.chunk_count == 2

    @pytest.mark.asyncio
    async def test_event_publishing(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        events: list = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = RetrievalEngine(store, embedding, event_publisher=publisher)
        await engine.search("hello")
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_custom_top_k(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": f"c{i}", "score": 1.0 - i * 0.1, "payload": {"document_id": "d1", "content": f"Chunk {i}", "chunk_index": i}}
            for i in range(20)
        ])
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)

        result = await engine.search("test", top_k=5)
        assert result.total_results <= 5
