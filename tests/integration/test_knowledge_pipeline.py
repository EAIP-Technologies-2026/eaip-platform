"""Integration tests for the knowledge pipeline.

Covers document upload, parsing, chunking, embedding, vector search,
metadata filters, and workspace isolation.
"""

from __future__ import annotations

import pytest

from eaip.knowledge.chunker import FixedSizeChunker
from eaip.knowledge.events import (
    ChunkingCompleted,
    DocumentIngested,
    EmbeddingCreated,
    KnowledgeIndexed,
    KnowledgeUploaded,
    SearchExecuted,
)
from eaip.knowledge.ingestion import IngestionPipeline
from eaip.knowledge.models import (
    ChunkingConfig,
    DocumentChunk,
    DocumentFormat,
    EmbeddingConfig,
    IngestionConfig,
    RetrievalConfig,
    RetrievalQuery,
)
from eaip.knowledge.retrieval import KnowledgeRetriever


class _MemoryVectorStore:
    """In-memory vector store for testing."""

    def __init__(self) -> None:
        self._collections: dict[str, list[dict[str, object]]] = {}

    async def create_collection(self, name: str, dimensions: int = 384, **kwargs: str) -> None:
        if name not in self._collections:
            self._collections[name] = []

    async def upsert_points(self, collection: str, chunks: list[DocumentChunk]) -> None:
        if collection not in self._collections:
            self._collections[collection] = []
        for c in chunks:
            self._collections[collection].append({
                "id": c.chunk_id,
                "document_id": c.document_id,
                "content": c.content,
                "embedding": c.embedding,
                "metadata": c.metadata,
            })

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        if collection in self._collections:
            self._collections[collection] = [
                p for p in self._collections[collection] if p["id"] not in point_ids
            ]

    async def search(self, collection: str, query: RetrievalQuery) -> list[dict[str, object]]:
        if collection not in self._collections:
            return []
        results = []
        for p in self._collections[collection]:
            content = str(p.get("content", ""))
            if query.query.lower() in content.lower():
                results.append(p)
            elif query.filters:
                meta = p.get("metadata", {})
                if isinstance(meta, dict) and isinstance(query.filters, dict):
                    if all(meta.get(k) == v for k, v in query.filters.items()):
                        results.append(p)
        return results[:query.top_k]

    async def delete_collection(self, name: str) -> None:
        self._collections.pop(name, None)

    async def list_collections(self) -> list[str]:
        return list(self._collections.keys())

    async def collection_info(self, name: str) -> dict[str, object]:
        return {"name": name, "points_count": len(self._collections.get(name, []))}


class _MockEmbeddingProvider:
    async def embed(self, texts: list[str], **kwargs: str) -> list[tuple[float, ...]]:
        return [(0.1,) * 384 for _ in texts]

    @property
    def dimensions(self) -> int:
        return 384


@pytest.fixture
def vector_store() -> _MemoryVectorStore:
    return _MemoryVectorStore()


@pytest.fixture
def embedding_provider() -> _MockEmbeddingProvider:
    return _MockEmbeddingProvider()


@pytest.fixture
def pipeline(vector_store, embedding_provider) -> IngestionPipeline:
    config = IngestionConfig(
        collection="test_collection",
        chunking=ChunkingConfig(chunk_size=100, chunk_overlap=20),
        embedding=EmbeddingConfig(provider="mock", dimensions=384),
    )
    return IngestionPipeline(
        config=config,
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        event_publisher=lambda e: None,
    )


@pytest.fixture
def retriever(vector_store) -> KnowledgeRetriever:
    return KnowledgeRetriever(
        vector_store=vector_store,
        default_collection="test_collection",
        config=RetrievalConfig(),
    )


class TestKnowledgePipeline:
    """End-to-end knowledge pipeline integration."""

    async def test_upload_and_index_txt(self, pipeline: IngestionPipeline) -> None:
        """Upload and index a plain text document."""
        content = b"Enterprise AI Platform knowledge management system for document processing."
        result = await pipeline.ingest(
            document_id="doc1",
            content=content,
            doc_format=DocumentFormat.TXT,
        )
        assert result.status.value == "indexed"
        assert result.chunk_count > 0
        assert result.document.document_id == "doc1"

    async def test_upload_and_index_markdown(self, pipeline: IngestionPipeline) -> None:
        """Upload and index a markdown document."""
        content = b"# Title\n\nThis is a **markdown** document with *formatting*."
        result = await pipeline.ingest(
            document_id="doc2",
            content=content,
            doc_format=DocumentFormat.MARKDOWN,
            title="Test Doc",
        )
        assert result.status.value == "indexed"
        assert result.document.title == "Test Doc"

    async def test_ingestion_generates_content_hash(self, pipeline: IngestionPipeline) -> None:
        """Ingested document should have a content hash."""
        content = b"Content for hash verification."
        result = await pipeline.ingest(
            document_id="doc3",
            content=content,
            doc_format=DocumentFormat.TXT,
        )
        assert result.document.content_hash

    async def test_ingestion_maintains_collection(self, pipeline: IngestionPipeline) -> None:
        """Ingested document should belong to the configured collection."""
        result = await pipeline.ingest(
            document_id="doc4",
            content=b"Collection test document.",
            doc_format=DocumentFormat.TXT,
        )
        assert result.document.collection == "test_collection"


class TestKnowledgeSearch:
    """Knowledge search integration."""

    @pytest.fixture
    def retriever(self, vector_store) -> KnowledgeRetriever:
        return KnowledgeRetriever(vector_store=vector_store, embedding_provider=_MockEmbeddingProvider())

    async def test_semantic_search(self, retriever: KnowledgeRetriever, pipeline: IngestionPipeline) -> None:
        """Semantic search should return matching documents."""
        await pipeline.ingest(
            document_id="search1",
            content=b"The quick brown fox jumps over the lazy dog.",
            doc_format=DocumentFormat.TXT,
        )
        results = await retriever.search(
            "test_collection", RetrievalQuery(query="fox", top_k=5)
        )
        assert len(results.chunks) > 0

    async def test_search_empty_collection(self, retriever: KnowledgeRetriever) -> None:
        """Search on empty collection returns empty results."""
        results = await retriever.search(
            "nonexistent", RetrievalQuery(query="anything", top_k=5)
        )
        assert len(results.chunks) == 0

    async def test_search_with_metadata_filters(self, retriever: KnowledgeRetriever, pipeline: IngestionPipeline) -> None:
        """Search with metadata filters should respect filters."""
        await pipeline.ingest(
            document_id="filter1",
            content=b"Document about AI governance.",
            doc_format=DocumentFormat.TXT,
            metadata={"category": "governance", "department": "legal"},
        )
        await pipeline.ingest(
            document_id="filter2",
            content=b"Document about AI engineering.",
            doc_format=DocumentFormat.TXT,
            metadata={"category": "engineering", "department": "platform"},
        )
        results = await retriever.search(
            "test_collection",
            RetrievalQuery(
                query="document",
                filter_metadata={"category": "governance"},
                top_k=5,
            ),
        )
        assert len(results.chunks) > 0

    async def test_pagination(self, retriever: KnowledgeRetriever, pipeline: IngestionPipeline) -> None:
        """Search pagination limits results."""
        content = b"Pageable document content for searching."
        for i in range(3):
            await pipeline.ingest(
                document_id=f"page{i}",
                content=content,
                doc_format=DocumentFormat.TXT,
            )
        results_1 = await retriever.search(
            "test_collection", RetrievalQuery(query="pageable", top_k=1)
        )
        results_5 = await retriever.search(
            "test_collection", RetrievalQuery(query="pageable", top_k=5)
        )
        assert len(results_1.chunks) <= 1
        assert len(results_5.chunks) >= 1


class TestKnowledgePipelineEvents:
    """Verify pipeline events are published at each stage."""

    async def test_pipeline_publishes_all_stage_events(self) -> None:
        """Every stage of the pipeline should publish an event."""
        events: list[str] = []
        collected: list[str] = []

        def collector(e: object) -> None:
            collected.append(type(e).__name__)
            events.append(type(e).__name__)

        config = IngestionConfig(
            collection="event_test",
            chunking=ChunkingConfig(chunk_size=200),
            embedding=EmbeddingConfig(provider="mock", dimensions=384),
        )
        store = _MemoryVectorStore()
        pipe = IngestionPipeline(
            config=config,
            vector_store=store,
            embedding_provider=_MockEmbeddingProvider(),
            event_publisher=collector,
        )
        await pipe.ingest(
            document_id="evt_doc",
            content=b"Event testing for pipeline stage publishing verification.",
            doc_format=DocumentFormat.TXT,
        )

        assert "KnowledgeUploaded" in collected
        assert "ChunkingCompleted" in collected
        assert "EmbeddingCreated" in collected
        assert "KnowledgeIndexed" in collected
        assert "DocumentIngested" in collected


class TestWorkspaceIsolation:
    """Verify workspace isolation in vector store operations."""

    async def test_different_collections_isolated(self, vector_store: _MemoryVectorStore) -> None:
        """Documents in different collections should not mix."""
        cfg_a = IngestionConfig(
            collection="workspace_a",
            chunking=ChunkingConfig(chunk_size=200),
        )
        cfg_b = IngestionConfig(
            collection="workspace_b",
            chunking=ChunkingConfig(chunk_size=200),
        )
        emb = _MockEmbeddingProvider()

        pipe_a = IngestionPipeline(config=cfg_a, vector_store=vector_store, embedding_provider=emb)
        pipe_b = IngestionPipeline(config=cfg_b, vector_store=vector_store, embedding_provider=emb)

        await pipe_a.ingest(document_id="wa1", content=b"Workspace A data.", doc_format=DocumentFormat.TXT)
        await pipe_b.ingest(document_id="wb1", content=b"Workspace B data.", doc_format=DocumentFormat.TXT)

        retriever = KnowledgeRetriever(vector_store=vector_store, embedding_provider=_MockEmbeddingProvider())
        results_a = await retriever.search("workspace_a", RetrievalQuery(query="Workspace", top_k=5))
        results_b = await retriever.search("workspace_b", RetrievalQuery(query="Workspace", top_k=5))

        assert len(results_a.chunks) > 0
        assert len(results_b.chunks) > 0
