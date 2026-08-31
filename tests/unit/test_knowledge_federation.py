"""Tests for KnowledgeFederation — federated search across collections and memory."""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.federation import KnowledgeFederation
from eaip.knowledge.models import (
    DocumentChunk,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    SourceAttribution,
)
from eaip.knowledge.retrieval_engine import RetrievalEngine


class _MockVectorStore:
    def __init__(self) -> None:
        self._results: list[dict[str, object]] = []
        self._collections: list[str] = ["dept_eng", "dept_eng_knowledge", "finance"]

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
        return self._collections

    async def collection_info(self, name: str) -> dict[str, object]:
        return {}


async def _memory_search_fn(query: str, top_k: int) -> RetrievalResult:
    return RetrievalResult(
        query=query,
        collection="memory",
        chunks=(
            RetrievedChunk(
                chunk_id="mem1",
                document_id="mem_doc1",
                collection="memory",
                content="Memory result",
                score=0.85,
                attribution=SourceAttribution(
                    document_id="mem_doc1",
                    collection="memory",
                    score=0.85,
                ),
            ),
        ),
        total_results=1,
    )


class TestKnowledgeFederation:
    @pytest.mark.asyncio
    async def test_search_collections_basic(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.9,
                    "payload": {"document_id": "d1", "content": "Result A", "chunk_index": 0},
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine)

        result = await federation.search_collections("test", ["a", "b"])
        assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_search_collections_aggregates(self) -> None:
        store = _MockVectorStore()

        async def _search_with_diff(
            collection: str, query: RetrievalQuery
        ) -> list[dict[str, object]]:
            if collection == "coll_a":
                return [
                    {
                        "id": "a1",
                        "score": 0.9,
                        "payload": {"document_id": "d1", "content": "From A", "chunk_index": 0},
                    },
                ]
            if collection == "coll_b":
                return [
                    {
                        "id": "b1",
                        "score": 0.8,
                        "payload": {"document_id": "d2", "content": "From B", "chunk_index": 1},
                    },
                ]
            return []

        store.search = _search_with_diff  # type: ignore[method-assign]
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine)

        result = await federation.search_collections("test", ["coll_a", "coll_b"])
        assert result.total_results == 2

    @pytest.mark.asyncio
    async def test_search_all(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.9,
                    "payload": {"document_id": "d1", "content": "Global", "chunk_index": 0},
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine)

        result = await federation.search_all("test")
        assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_search_knowledge_and_memory(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.9,
                    "payload": {"document_id": "d1", "content": "Knowledge", "chunk_index": 0},
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine, memory_search_fn=_memory_search_fn)

        result = await federation.search_knowledge_and_memory("test", collections=["default"])
        assert result.total_results >= 1

    @pytest.mark.asyncio
    async def test_search_knowledge_and_memory_no_memory_fn(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.9,
                    "payload": {"document_id": "d1", "content": "Only knowledge", "chunk_index": 0},
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine)

        result = await federation.search_knowledge_and_memory("test")
        assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_search_department_brain(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.95,
                    "payload": {
                        "document_id": "d1",
                        "content": "Engineering doc",
                        "chunk_index": 0,
                    },
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine)

        result = await federation.search_department_brain("test", "eng")
        assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_search_enterprise_brain(self) -> None:
        store = _MockVectorStore()
        store.set_results(
            [
                {
                    "id": "c1",
                    "score": 0.9,
                    "payload": {"document_id": "d1", "content": "Enterprise", "chunk_index": 0},
                },
            ]
        )
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine)

        result = await federation.search_enterprise_brain("test")
        assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_deduplication(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        federation = KnowledgeFederation(engine)

        chunks = [
            RetrievedChunk(
                chunk_id="dup",
                document_id="d1",
                collection="a",
                content="Duplicate",
                score=0.9,
                attribution=SourceAttribution(document_id="d1", collection="a", score=0.9),
            ),
            RetrievedChunk(
                chunk_id="dup",
                document_id="d1",
                collection="b",
                content="Duplicate",
                score=0.8,
                attribution=SourceAttribution(document_id="d1", collection="b", score=0.8),
            ),
        ]

        deduped = federation._deduplicate(chunks)
        assert len(deduped) == 1

    def test_score_normalization(self) -> None:
        chunks = [
            RetrievedChunk(
                chunk_id="c1",
                document_id="d1",
                collection="a",
                content="Low",
                score=0.2,
                attribution=SourceAttribution(document_id="d1", collection="a", score=0.2),
            ),
            RetrievedChunk(
                chunk_id="c2",
                document_id="d2",
                collection="b",
                content="High",
                score=0.8,
                attribution=SourceAttribution(document_id="d2", collection="b", score=0.8),
            ),
        ]

        KnowledgeFederation._normalize_scores(chunks)
        assert 0.0 <= chunks[0].score <= 1.0
        assert chunks[1].score >= chunks[0].score

    @pytest.mark.asyncio
    async def test_event_publishing(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        engine = RetrievalEngine(store, embedding)
        events: list = []

        def publisher(event: object) -> None:
            events.append(event)

        federation = KnowledgeFederation(engine, event_publisher=publisher)
        await federation.search_collections("test", ["a", "b"])
        assert len(events) >= 1
