"""Knowledge Engine — document ingestion, vector indexing, hybrid retrieval.

Bundle-016 of the EAIP Platform Foundation Milestone.

Provides:
- Knowledge Provider Interface & Models
- Document ingestion pipeline (PDF, DOCX, MD, HTML, TXT)
- Configurable chunking strategies (fixed-size, semantic, recursive)
- Embedding generation through the Provider Framework
- Qdrant vector store integration
- Metadata indexing and hybrid semantic retrieval
- Context assembly with source attribution
- Knowledge collections management
- Incremental indexing and event-driven ingestion
- Policy-aware knowledge access
- Plugin, Runtime, Capability Registry, Metrics and Health integration
"""

from __future__ import annotations

from eaip.knowledge.base import (
    Chunker,
    DocumentParser,
    EmbeddingProvider,
    KnowledgeProvider,
    VectorStore,
)
from eaip.knowledge.chunker import (
    FixedSizeChunker,
    RecursiveChunker,
    SemanticChunker,
    create_chunker,
)
from eaip.knowledge.discovery import KnowledgeDiscovery
from eaip.knowledge.embedding import MockEmbeddingProvider, ProviderEmbedding
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.events import (
    CollectionCreated,
    CollectionDeleted,
    DocumentDeleted,
    DocumentIngested,
    KnowledgeQuery,
    RetrievalExecuted,
)
from eaip.knowledge.exceptions import (
    ChunkingError,
    CollectionNotFoundError,
    DocumentNotFoundError,
    DocumentParseError,
    EmbeddingError,
    IngestionError,
    KnowledgeError,
    RetrievalError,
    UnsupportedFormatError,
)
from eaip.knowledge.health import KnowledgeHealthCheck
from eaip.knowledge.ingestion import (
    DOCXParser,
    HTMLParser,
    IngestionPipeline,
    MarkdownParser,
    PDFParser,
    TextParser,
    get_parser,
    register_parser,
)
from eaip.knowledge.integration import KnowledgeRuntimeModule
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
from eaip.knowledge.qdrant_store import QdrantStore
from eaip.knowledge.registry import KnowledgeRegistry
from eaip.knowledge.retrieval import KnowledgeRetriever

__all__ = [
    "AssembledContext",
    "Chunker",
    "ChunkingConfig",
    "ChunkingError",
    "ChunkingStrategy",
    "CollectionCreated",
    "CollectionDeleted",
    "CollectionNotFoundError",
    "DOCXParser",
    "DocumentChunk",
    "DocumentDeleted",
    "DocumentFormat",
    "DocumentIngested",
    "DocumentNotFoundError",
    "DocumentParseError",
    "DocumentParser",
    "EmbeddingConfig",
    "EmbeddingError",
    "EmbeddingProvider",
    "FixedSizeChunker",
    "HTMLParser",
    "IndexingStatus",
    "IngestionConfig",
    "IngestionError",
    "IngestionPipeline",
    "IngestionResult",
    "KnowledgeCollection",
    "KnowledgeDiscovery",
    "KnowledgeDocument",
    "KnowledgeEngine",
    "KnowledgeError",
    "KnowledgeHealthCheck",
    "KnowledgeProvider",
    "KnowledgeQuery",
    "KnowledgeRegistry",
    "KnowledgeRetriever",
    "KnowledgeRuntimeModule",
    "MarkdownParser",
    "MockEmbeddingProvider",
    "PDFParser",
    "ProviderEmbedding",
    "QdrantStore",
    "RecursiveChunker",
    "RetrievalError",
    "RetrievalExecuted",
    "RetrievalQuery",
    "RetrievalResult",
    "RetrievedChunk",
    "SemanticChunker",
    "SourceAttribution",
    "TextParser",
    "UnsupportedFormatError",
    "VectorStore",
    "create_chunker",
    "get_parser",
    "register_parser",
]
