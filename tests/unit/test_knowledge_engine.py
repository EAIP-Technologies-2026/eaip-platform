"""Tests for the KnowledgeEngine orchestrator."""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.exceptions import CollectionNotFoundError, KnowledgeError
from eaip.knowledge.models import (
    DocumentChunk,
    DocumentFormat,
    RetrievalQuery,
)
from eaip.knowledge.registry import KnowledgeRegistry


class _MockVectorStore:
    def __init__(self) -> None:
        self.collections: dict[str, int] = {}
        self.points: dict[str, list[DocumentChunk]] = {}

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        self.collections[name] = dimensions

    async def upsert_points(self, collection: str, chunks: list[DocumentChunk]) -> None:
        if collection not in self.points:
            self.points[collection] = []
        self.points[collection].extend(chunks)

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        if collection in self.points:
            self.points[collection] = [
                p for p in self.points[collection] if p.chunk_id not in point_ids
            ]

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict[str, object]]:
        return []

    async def delete_collection(self, name: str) -> None:
        self.collections.pop(name, None)
        self.points.pop(name, None)

    async def list_collections(self) -> list[str]:
        return list(self.collections.keys())

    async def collection_info(self, name: str) -> dict[str, object]:
        return {"name": name, "status": "green", "vectors_count": len(self.points.get(name, []))}


class TestKnowledgeEngine:
    @pytest.mark.asyncio
    async def test_create_collection(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        col = await engine.create_collection("test-col")
        assert col.name == "test-col"
        assert reg.has_collection("test-col")

    @pytest.mark.asyncio
    async def test_create_duplicate_collection_raises(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.create_collection("dup")
        with pytest.raises(KnowledgeError):
            await engine.create_collection("dup")

    @pytest.mark.asyncio
    async def test_delete_collection(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.create_collection("to-delete")
        assert await engine.delete_collection("to-delete")
        assert not reg.has_collection("to-delete")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_collection(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        assert not await engine.delete_collection("nonexistent")

    @pytest.mark.asyncio
    async def test_list_collections(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.create_collection("a")
        await engine.create_collection("b")
        cols = await engine.list_collections()
        assert len(cols) == 2

    @pytest.mark.asyncio
    async def test_get_collection(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.create_collection("my-col")
        col = await engine.get_collection("my-col")
        assert col.name == "my-col"

    @pytest.mark.asyncio
    async def test_get_nonexistent_collection_raises(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        with pytest.raises(CollectionNotFoundError):
            await engine.get_collection("nonexistent")

    @pytest.mark.asyncio
    async def test_ingest_document(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        result = await engine.ingest(
            "doc1", b"Hello world content", DocumentFormat.TXT, title="Test"
        )
        assert result.document.document_id == "doc1"
        assert reg.has_document("doc1", "default")
        assert "default" in vs.collections

    @pytest.mark.asyncio
    async def test_ingest_into_existing_collection(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.create_collection("docs")
        result = await engine.ingest("doc1", b"Content", DocumentFormat.TXT, collection="docs")
        assert result.document.collection == "docs"

    @pytest.mark.asyncio
    async def test_delete_document(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.ingest("doc1", b"Content to delete", DocumentFormat.TXT, title="Del")
        assert await engine.delete_document("doc1", "default")
        assert not reg.has_document("doc1", "default")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        assert not await engine.delete_document("nonexistent")

    @pytest.mark.asyncio
    async def test_query_nonexistent_collection_raises(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        with pytest.raises(CollectionNotFoundError):
            await engine.query("test", collection="nonexistent")

    @pytest.mark.asyncio
    async def test_query_empty_collection(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.create_collection("empty")
        result = await engine.query("test query", collection="empty")
        assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_search_multi(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, vs, ep)

        await engine.create_collection("a")
        await engine.create_collection("b")
        results = await engine.search_multi("test query", ["a", "b"])
        assert "a" in results
        assert "b" in results

    @pytest.mark.asyncio
    async def test_authorization(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        denied: list[str] = []

        def authorize(action: str, resource: str) -> None:
            if action == "deny":
                raise KnowledgeError("Access denied")
            denied.append(action)

        engine = KnowledgeEngine(reg, vs, ep, authorize_fn=authorize)
        await engine.create_collection("auth")
        await engine.ingest("doc1", b"Content", DocumentFormat.TXT, collection="auth")
        result = await engine.query("test", collection="auth", subject_id="user1")
        assert result.total_results == 0

    @pytest.mark.asyncio
    async def test_event_publishing(self) -> None:
        reg = KnowledgeRegistry()
        vs = _MockVectorStore()
        ep = MockEmbeddingProvider()
        events: list = []

        def publisher(event: object) -> None:
            events.append(event)

        engine = KnowledgeEngine(reg, vs, ep, event_publisher=publisher)
        await engine.create_collection("evt")
        await engine.ingest("doc1", b"Content", DocumentFormat.TXT, collection="evt")
        assert len(events) >= 1
