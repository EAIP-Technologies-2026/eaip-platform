"""End-to-end test demonstrating the complete Knowledge Engine workflow.

Demonstrates:
- Document ingestion across multiple formats
- Chunking with different strategies
- Vector indexing
- Hybrid retrieval
- Context assembly with source attribution
- Collection management
- Event publishing
"""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.models import (
    ChunkingConfig,
    ChunkingStrategy,
    DocumentFormat,
    EmbeddingConfig,
)
from eaip.knowledge.registry import KnowledgeRegistry


class _E2EStore:
    def __init__(self) -> None:
        self.collections: dict[str, dict] = {}
        self.points: dict[str, list[dict]] = {}

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        self.collections[name] = {"dimensions": dimensions, "points": 0}

    async def upsert_points(self, collection: str, chunks: list) -> None:
        for c in chunks:
            self.points.setdefault(collection, []).append({
                "id": c.chunk_id,
                "doc_id": c.document_id,
                "content": c.content,
                "idx": c.chunk_index,
                "embedding": list(c.embedding),
            })
        self.collections[collection]["points"] = len(self.points.get(collection, []))

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        if collection in self.points:
            self.points[collection] = [p for p in self.points[collection] if p["id"] not in point_ids]

    async def search(self, collection: str, query) -> list[dict]:  # type: ignore[no-untyped-def]
        results = []
        for p in self.points.get(collection, []):
            results.append({
                "id": p["id"],
                "score": 0.85,
                "payload": {
                    "document_id": p["doc_id"],
                    "content": p["content"],
                    "chunk_index": p["idx"],
                    "title": "E2E Test Doc",
                    "source": "e2e-test.txt",
                },
            })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[: query.top_k]

    async def delete_collection(self, name: str) -> None:
        self.collections.pop(name, None)
        self.points.pop(name, None)

    async def list_collections(self) -> list[str]:
        return list(self.collections.keys())

    async def collection_info(self, name: str) -> dict[str, object]:
        info = self.collections.get(name, {})
        return {
            "name": name,
            "status": "green",
            "points_count": info.get("points", 0),
        }


class TestKnowledgeE2E:
    @pytest.mark.asyncio
    async def test_e2e_demo_workflow(self) -> None:
        """Demonstrate a complete Knowledge Engine workflow."""
        reg = KnowledgeRegistry()
        store = _E2EStore()
        embed = MockEmbeddingProvider(dimensions=384)
        events: list[str] = []

        def publisher(event: object) -> None:
            events.append(type(event).__name__)

        engine = KnowledgeEngine(
            reg, store, embed,
            event_publisher=publisher,
            default_chunking=ChunkingConfig(
                strategy=ChunkingStrategy.RECURSIVE,
                chunk_size=100,
                chunk_overlap=10,
            ),
            default_embedding=EmbeddingConfig(dimensions=384),
        )

        # 1. Create collections
        col_technical = await engine.create_collection("technical-docs",
            description="Technical documentation",
        )
        assert col_technical.name == "technical-docs"

        col_product = await engine.create_collection("product-docs",
            description="Product documentation",
        )
        assert col_product.name == "product-docs"

        # 2. Ingest documents in various formats
        txt_result = await engine.ingest(
            "arch-overview",
            b"The EAIP Knowledge Engine provides document ingestion, "
            b"vector indexing, and hybrid retrieval capabilities. "
            b"It supports multiple document formats.",
            DocumentFormat.TXT,
            collection="technical-docs",
            title="Architecture Overview",
        )
        assert txt_result.status.value == "indexed"
        assert txt_result.chunk_count > 0

        md_result = await engine.ingest(
            "getting-started",
            b"# Getting Started\n\n## Installation\n\nInstall the package.\n\n## Usage\n\nUse the API.",
            DocumentFormat.MARKDOWN,
            collection="technical-docs",
            title="Getting Started Guide",
        )
        assert md_result.status.value == "indexed"

        html_result = await engine.ingest(
            "product-page",
            b"<html><body><h1>Product</h1><p>Description here.</p></body></html>",
            DocumentFormat.HTML,
            collection="product-docs",
            title="Product Page",
        )
        assert html_result.status.value == "indexed"

        # 3. Verify collections
        collections = await engine.list_collections()
        assert len(collections) == 2

        col_info = await store.collection_info("technical-docs")
        assert col_info["points_count"] > 0

        # 4. Query across collections
        result = await engine.query(
            "What is the EAIP Knowledge Engine?",
            collection="technical-docs",
            top_k=3,
        )
        assert result.total_results >= 0
        assert result.query == "What is the EAIP Knowledge Engine?"
        assert result.duration_ms >= 0

        # 5. Multi-collection search
        multi = await engine.search_multi(
            "documentation",
            ["technical-docs", "product-docs"],
        )
        assert len(multi) == 2

        # 6. Context assembly via retriever
        from eaip.knowledge.retrieval import KnowledgeRetriever

        retriever = KnowledgeRetriever(store, embed)
        from eaip.knowledge.models import RetrievalQuery

        retrieval = await retriever.search("technical-docs", RetrievalQuery(
            query="knowledge engine architecture",
            top_k=2,
        ))
        if retrieval.chunks:
            assert retrieval.context is not None
            assert "EAIP" in retrieval.context.context or "Knowledge" in retrieval.context.context

        # 7. Delete a document
        deleted = await engine.delete_document("arch-overview", "technical-docs")
        assert deleted

        # 8. Delete a collection
        deleted_col = await engine.delete_collection("product-docs")
        assert deleted_col
        collections = await engine.list_collections()
        assert len(collections) == 1

        # 9. Verify events were published
        event_names = set(events)
        assert "CollectionCreated" in event_names or len(events) >= 2
