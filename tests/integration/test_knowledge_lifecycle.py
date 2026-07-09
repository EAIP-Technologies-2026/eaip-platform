"""Integration tests for Knowledge Engine lifecycle and end-to-end flow."""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.models import (
    ChunkingConfig,
    ChunkingStrategy,
    DocumentFormat,
    EmbeddingConfig,
    KnowledgeCollection,
    RetrievalQuery,
)
from eaip.knowledge.qdrant_store import QdrantStore
from eaip.knowledge.registry import KnowledgeRegistry


class _MemStore:
    """In-memory vector store for integration testing."""

    def __init__(self) -> None:
        self.collections: dict[str, dict] = {}
        self.points: dict[str, list[dict]] = {}

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        self.collections[name] = {"dimensions": dimensions, "status": "green"}
        if name not in self.points:
            self.points[name] = []

    async def upsert_points(self, collection: str, chunks: list) -> None:
        from eaip.knowledge.models import DocumentChunk

        for c in chunks:
            self.points.setdefault(collection, []).append({
                "id": c.chunk_id,
                "document_id": c.document_id,
                "content": c.content,
                "chunk_index": c.chunk_index,
                "embedding": list(c.embedding),
                "score": 1.0,
            })

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        self.points[collection] = [p for p in self.points.get(collection, []) if p["id"] not in point_ids]

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict]:
        results = []
        for p in self.points.get(collection, []):
            results.append({
                "id": p["id"],
                "score": p.get("score", 0.5),
                "payload": {
                    "document_id": p["document_id"],
                    "content": p["content"],
                    "chunk_index": p["chunk_index"],
                    "title": "Test Doc",
                    "source": "test.txt",
                },
            })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[: query.top_k]

    async def delete_collection(self, name: str) -> None:
        self.collections.pop(name, None)
        self.points.pop(name, None)

    async def list_collections(self) -> list[str]:
        return list(self.collections.keys())

    async def collection_info(self, name: str) -> dict:
        info = self.collections.get(name, {})
        return {
            "name": name,
            "status": info.get("status", "red"),
            "points_count": len(self.points.get(name, [])),
        }


class TestKnowledgeLifecycleIntegration:
    @pytest.mark.asyncio
    async def test_full_ingest_and_retrieve_flow(self) -> None:
        reg = KnowledgeRegistry()
        store = _MemStore()
        embed = MockEmbeddingProvider(dimensions=384)
        engine = KnowledgeEngine(reg, store, embed)

        col = await engine.create_collection("integration-test")
        assert col.name == "integration-test"

        result = await engine.ingest(
            "doc1",
            b"Enterprise AI Platform Knowledge Engine. This document describes the architecture.",
            DocumentFormat.TXT,
            collection="integration-test",
            title="Architecture Overview",
        )
        assert result.status.value == "indexed"
        assert result.chunk_count > 0

        result = await engine.ingest(
            "doc2",
            b"Vector search enables hybrid retrieval combining dense and sparse approaches.",
            DocumentFormat.TXT,
            collection="integration-test",
            title="Vector Search",
        )
        assert result.status.value == "indexed"

        query_result = await engine.query(
            "hybrid vector retrieval",
            collection="integration-test",
            top_k=3,
        )
        assert query_result.total_results >= 0
        assert query_result.query == "hybrid vector retrieval"

    @pytest.mark.asyncio
    async def test_multiple_collections(self) -> None:
        reg = KnowledgeRegistry()
        store = _MemStore()
        embed = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, store, embed)

        await engine.create_collection("docs")
        await engine.create_collection("manuals")

        await engine.ingest("d1", b"Docs content", DocumentFormat.TXT, collection="docs")
        await engine.ingest("m1", b"Manual content", DocumentFormat.TXT, collection="manuals")

        results = await engine.search_multi("content", ["docs", "manuals"])
        assert "docs" in results
        assert "manuals" in results

    @pytest.mark.asyncio
    async def test_document_lifecycle(self) -> None:
        reg = KnowledgeRegistry()
        store = _MemStore()
        embed = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, store, embed)

        await engine.create_collection("lifecycle")
        await engine.ingest("d1", b"Content to delete", DocumentFormat.TXT, collection="lifecycle")
        assert reg.has_document("d1", "lifecycle")

        deleted = await engine.delete_document("d1", "lifecycle")
        assert deleted
        assert not reg.has_document("d1", "lifecycle")

    @pytest.mark.asyncio
    async def test_chunking_configs(self) -> None:
        reg = KnowledgeRegistry()
        store = _MemStore()
        embed = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, store, embed, default_chunking=ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=30,
        ))

        await engine.create_collection("chunk-test")
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three.\n\nParagraph four."
        result = await engine.ingest("d1", text.encode(), DocumentFormat.TXT, collection="chunk-test")
        assert result.chunk_count >= 2

    @pytest.mark.asyncio
    async def test_embedding_config(self) -> None:
        reg = KnowledgeRegistry()
        store = _MemStore()
        embed = MockEmbeddingProvider(dimensions=768)
        engine = KnowledgeEngine(reg, store, embed, default_embedding=EmbeddingConfig(
            dimensions=768,
            model="test-model",
        ))

        col = await engine.create_collection("embed-test", embedding_config=EmbeddingConfig(dimensions=768))
        assert col.embedding_config.dimensions == 768

    @pytest.mark.asyncio
    async def test_collection_info(self) -> None:
        reg = KnowledgeRegistry()
        store = _MemStore()
        embed = MockEmbeddingProvider()
        engine = KnowledgeEngine(reg, store, embed)

        await engine.create_collection("info-test")
        info = await store.collection_info("info-test")
        assert info["status"] == "green"
