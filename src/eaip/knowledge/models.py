"""Knowledge Engine models — documents, chunks, collections, queries, results."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DocumentFormat(StrEnum):
    """Supported document formats for ingestion."""

    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    HTML = "html"
    TXT = "txt"


class ChunkingStrategy(StrEnum):
    """Strategies for splitting documents into chunks."""

    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"


class ChunkingConfig(BaseModel):
    """Configuration for document chunking."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = 512
    chunk_overlap: int = 64
    separators: tuple[str, ...] = ("\n\n", "\n", ".", " ", "")
    max_chunks: int = 0


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str = ""
    model: str = ""
    dimensions: int = 384
    batch_size: int = 32


class IndexingStatus(StrEnum):
    """Status of a document indexing operation."""

    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class KnowledgeDocument(BaseModel):
    """A source document ingested into the Knowledge Engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    collection: str
    format: DocumentFormat
    title: str = ""
    source: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    indexing_status: IndexingStatus = IndexingStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    content_hash: str = ""
    chunk_count: int = 0


class DocumentChunk(BaseModel):
    """A single chunk extracted from a source document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    document_id: str
    collection: str
    content: str
    content_hash: str = ""
    chunk_index: int = 0
    embedding: tuple[float, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeCollection(BaseModel):
    """A named collection of knowledge documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    collection_id: str
    name: str
    description: str = ""
    embedding_config: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    chunking_config: ChunkingConfig = Field(default_factory=ChunkingConfig)
    document_count: int = 0
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalQuery(BaseModel):
    """A query against the knowledge store."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    collection: str = ""
    top_k: int = 5
    score_threshold: float = 0.0
    filter_metadata: dict[str, Any] = Field(default_factory=dict)
    include_embeddings: bool = False
    hybrid: bool = True
    alpha: float = 0.5
    vector: tuple[float, ...] = ()


class RetrievalConfig(BaseModel):
    """Configuration for retrieval operations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    collection: str = "default"
    top_k: int = 10
    score_threshold: float = 0.0


class SourceAttribution(BaseModel):
    """Attribution for a piece of retrieved content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    document_title: str = ""
    collection: str
    chunk_index: int = 0
    source: str = ""
    score: float = 0.0


class RetrievedChunk(BaseModel):
    """A chunk returned from a retrieval query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    document_id: str
    collection: str
    content: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    attribution: SourceAttribution | None = None


class AssembledContext(BaseModel):
    """Assembled context built from retrieved chunks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    context: str
    chunks: tuple[RetrievedChunk, ...] = ()
    token_estimate: int = 0
    chunk_count: int = 0


class RetrievalResult(BaseModel):
    """Complete result from a knowledge retrieval query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    collection: str = ""
    chunks: tuple[RetrievedChunk, ...] = ()
    context: AssembledContext | None = None
    total_results: int = 0
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=utc_now)


class IngestionResult(BaseModel):
    """Result of a document ingestion operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: KnowledgeDocument
    chunk_count: int = 0
    status: IndexingStatus = IndexingStatus.INDEXED
    duration_ms: float = 0.0
    errors: tuple[str, ...] = ()


class IngestionConfig(BaseModel):
    """Configuration for document ingestion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    collection: str = "default"
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    extract_metadata: bool = True
    generate_hash: bool = True


__all__ = [
    "AssembledContext",
    "ChunkingConfig",
    "ChunkingStrategy",
    "DocumentChunk",
    "DocumentFormat",
    "EmbeddingConfig",
    "IndexingStatus",
    "IngestionConfig",
    "IngestionResult",
    "KnowledgeCollection",
    "KnowledgeDocument",
    "RetrievalConfig",
    "RetrievalQuery",
    "RetrievalResult",
    "RetrievedChunk",
    "SourceAttribution",
]
