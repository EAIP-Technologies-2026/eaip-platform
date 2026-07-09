from __future__ import annotations

from eaip.knowledge.models import (
    AssembledContext,
    ChunkingConfig,
    ChunkingStrategy,
    DocumentChunk,
    DocumentFormat,
    EmbeddingConfig,
    IndexingStatus,
    IngestionConfig,
    IngestionResult,
    KnowledgeCollection,
    KnowledgeDocument,
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
    SourceAttribution,
)


class TestDocumentModels:
    def test_knowledge_document_defaults(self) -> None:
        doc = KnowledgeDocument(document_id="doc1", collection="default", format=DocumentFormat.TXT)
        assert doc.document_id == "doc1"
        assert doc.collection == "default"
        assert doc.format is DocumentFormat.TXT
        assert doc.indexing_status is IndexingStatus.PENDING
        assert doc.title == ""
        assert doc.chunk_count == 0

    def test_document_chunk_defaults(self) -> None:
        chunk = DocumentChunk(chunk_id="chunk1", document_id="doc1", collection="default", content="hello")
        assert chunk.chunk_id == "chunk1"
        assert chunk.content == "hello"
        assert chunk.chunk_index == 0
        assert chunk.embedding == ()

    def test_document_chunk_with_embedding(self) -> None:
        emb = (0.1, 0.2, 0.3)
        chunk = DocumentChunk(
            chunk_id="chunk1", document_id="doc1", collection="default",
            content="hello", embedding=emb,
        )
        assert chunk.embedding == emb


class TestCollectionModels:
    def test_knowledge_collection_defaults(self) -> None:
        col = KnowledgeCollection(collection_id="col:default", name="default")
        assert col.name == "default"
        assert col.document_count == 0
        assert col.embedding_config.dimensions == 384
        assert col.chunking_config.strategy is ChunkingStrategy.FIXED_SIZE

    def test_knowledge_collection_with_config(self) -> None:
        col = KnowledgeCollection(
            collection_id="col:docs", name="docs",
            description="Documentation",
            embedding_config=EmbeddingConfig(dimensions=768, model="text-embedding-3"),
            chunking_config=ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC, chunk_size=1024),
        )
        assert col.embedding_config.dimensions == 768
        assert col.chunking_config.chunk_size == 1024
        assert col.chunking_config.strategy is ChunkingStrategy.SEMANTIC


class TestRetrievalModels:
    def test_retrieval_query_defaults(self) -> None:
        q = RetrievalQuery(query="test query")
        assert q.query == "test query"
        assert q.top_k == 5
        assert q.hybrid is True

    def test_retrieved_chunk_with_attribution(self) -> None:
        attr = SourceAttribution(
            document_id="doc1", document_title="Test Doc",
            collection="default", chunk_index=0, score=0.95,
        )
        chunk = RetrievedChunk(
            chunk_id="ch1", document_id="doc1",
            collection="default", content="content", score=0.95,
            attribution=attr,
        )
        assert chunk.attribution is not None
        assert chunk.attribution.document_title == "Test Doc"

    def test_assembled_context(self) -> None:
        ctx = AssembledContext(context="some context", chunk_count=3, token_estimate=50)
        assert ctx.context == "some context"
        assert ctx.chunk_count == 3
        assert ctx.token_estimate == 50


class TestIngestionModels:
    def test_ingestion_result_defaults(self) -> None:
        doc = KnowledgeDocument(document_id="d1", collection="c", format=DocumentFormat.TXT)
        result = IngestionResult(document=doc)
        assert result.status is IndexingStatus.INDEXED
        assert result.chunk_count == 0
        assert result.errors == ()

    def test_ingestion_result_with_errors(self) -> None:
        doc = KnowledgeDocument(
            document_id="d1", collection="c", format=DocumentFormat.PDF,
            indexing_status=IndexingStatus.FAILED,
        )
        result = IngestionResult(document=doc, status=IndexingStatus.FAILED, errors=("bad format",))
        assert result.status is IndexingStatus.FAILED
        assert "bad format" in result.errors


class TestChunkingConfig:
    def test_defaults(self) -> None:
        cfg = ChunkingConfig()
        assert cfg.strategy is ChunkingStrategy.FIXED_SIZE
        assert cfg.chunk_size == 512
        assert cfg.chunk_overlap == 64

    def test_recursive_config(self) -> None:
        cfg = ChunkingConfig(
            strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=256,
            chunk_overlap=32,
            separators=("\n", ".", " "),
        )
        assert cfg.strategy is ChunkingStrategy.RECURSIVE
        assert cfg.separators == ("\n", ".", " ")
