"""Tests for knowledge retrieval, context assembly, and source attribution."""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.models import (
    DocumentChunk,
    RetrievalQuery,
    RetrievedChunk,
    SourceAttribution,
)
from eaip.knowledge.retrieval import KnowledgeRetriever


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


class TestKnowledgeRetriever:
    @pytest.mark.asyncio
    async def test_search_empty(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        retriever = KnowledgeRetriever(store, embedding)

        result = await retriever.search("test", RetrievalQuery(query="hello"))
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
                },
            },
        ])
        embedding = MockEmbeddingProvider()
        retriever = KnowledgeRetriever(store, embedding)

        result = await retriever.search("test", RetrievalQuery(query="test query"))
        assert result.total_results == 1
        assert result.chunks[0].content == "Test content"
        assert result.chunks[0].score == 0.95
        assert result.chunks[0].attribution is not None
        assert result.chunks[0].attribution.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_search_multi(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.9, "payload": {"document_id": "d1", "content": "A", "chunk_index": 0}},
        ])
        embedding = MockEmbeddingProvider()
        retriever = KnowledgeRetriever(store, embedding)

        results = await retriever.search_multi(["col1", "col2"], RetrievalQuery(query="test"))
        assert "col1" in results
        assert "col2" in results

    @pytest.mark.asyncio
    async def test_search_filters_empty_payload(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.8, "payload": {}},
        ])
        embedding = MockEmbeddingProvider()
        retriever = KnowledgeRetriever(store, embedding)

        result = await retriever.search("test", RetrievalQuery(query="q"))
        assert result.total_results == 1

    @pytest.mark.asyncio
    async def test_search_no_payload(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {"id": "c1", "score": 0.8},
        ])
        embedding = MockEmbeddingProvider()
        retriever = KnowledgeRetriever(store, embedding)

        result = await retriever.search("test", RetrievalQuery(query="q"))
        assert result.total_results == 1


class TestContextAssembly:
    @pytest.mark.asyncio
    async def test_assemble_context(self) -> None:
        store = _MockVectorStore()
        store.set_results([
            {
                "id": "c1",
                "score": 0.95,
                "payload": {"document_id": "d1", "content": "First chunk", "chunk_index": 0, "title": "Doc 1"},
            },
            {
                "id": "c2",
                "score": 0.85,
                "payload": {"document_id": "d2", "content": "Second chunk", "chunk_index": 1, "source": "path/to/file"},
            },
        ])
        embedding = MockEmbeddingProvider()
        retriever = KnowledgeRetriever(store, embedding)

        result = await retriever.search("test", RetrievalQuery(query="test"))
        context = result.context
        assert context is not None
        assert "First chunk" in context.context
        assert "Second chunk" in context.context
        assert context.chunk_count == 2
        assert context.token_estimate > 0

    @pytest.mark.asyncio
    async def test_assemble_context_empty(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        retriever = KnowledgeRetriever(store, embedding)

        result = await retriever.search("test", RetrievalQuery(query="test"))
        assert result.context is None


class TestSourceAttribution:
    def test_attribution_fields(self) -> None:
        attr = SourceAttribution(
            document_id="doc1",
            document_title="My Document",
            collection="default",
            chunk_index=3,
            source="/path/to/doc.pdf",
            score=0.92,
        )
        assert attr.document_id == "doc1"
        assert attr.document_title == "My Document"
        assert attr.source == "/path/to/doc.pdf"
        assert attr.score == 0.92
        assert attr.chunk_index == 3
