"""Knowledge Engine — document ingestion, vector indexing, hybrid retrieval,
and RAG orchestration.

Bundle-016 / Bundle-026 of the EAIP Platform Foundation Milestone.

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
- RetrievalEngine — hybrid search (semantic + keyword), reranking, multi-collection
- Search strategies — semantic, keyword, hybrid, reranking protocols
- KnowledgeFederation — federated search across collections, memory, departments
- Retrieval policies — access control and policy enforcement
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
    FederatedSearchExecuted,
    HybridSearchExecuted,
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
from eaip.knowledge.federation import KnowledgeFederation
from eaip.knowledge.health import KnowledgeHealthCheck
from eaip.knowledge.in_memory_store import InMemoryVectorStore
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
from eaip.knowledge.policies import (
    AccessLevel,
    CollectionAccessPolicy,
    PolicyResolver,
    RetrievalPolicy,
    RetrievalPolicyEnforcer,
)
from eaip.knowledge.qdrant_store import QdrantStore
from eaip.knowledge.registry import KnowledgeRegistry
from eaip.knowledge.retrieval import KnowledgeRetriever
from eaip.knowledge.retrieval_engine import RetrievalEngine
from eaip.knowledge.search_strategies import (
    CrossEncoderReranker,
    HybridSearchStrategy,
    KeywordSearchStrategy,
    RerankingStrategy,
    SearchStrategy,
    SemanticSearchStrategy,
    SimpleReranker,
)

__all__ = [
    "AccessLevel",
    "AssembledContext",
    "Chunker",
    "ChunkingConfig",
    "ChunkingError",
    "ChunkingStrategy",
    "CollectionAccessPolicy",
    "CollectionCreated",
    "CollectionDeleted",
    "CollectionNotFoundError",
    "CrossEncoderReranker",
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
    "FederatedSearchExecuted",
    "FixedSizeChunker",
    "HTMLParser",
    "HybridSearchExecuted",
    "HybridSearchStrategy",
    "InMemoryVectorStore",
    "IndexingStatus",
    "IngestionConfig",
    "IngestionError",
    "IngestionPipeline",
    "IngestionResult",
    "KeywordSearchStrategy",
    "KnowledgeCollection",
    "KnowledgeDiscovery",
    "KnowledgeDocument",
    "KnowledgeEngine",
    "KnowledgeError",
    "KnowledgeFederation",
    "KnowledgeHealthCheck",
    "KnowledgeProvider",
    "KnowledgeQuery",
    "KnowledgeRegistry",
    "KnowledgeRetriever",
    "KnowledgeRuntimeModule",
    "MarkdownParser",
    "MockEmbeddingProvider",
    "PDFParser",
    "PolicyResolver",
    "ProviderEmbedding",
    "QdrantStore",
    "RecursiveChunker",
    "RerankingStrategy",
    "RetrievalEngine",
    "RetrievalError",
    "RetrievalExecuted",
    "RetrievalPolicy",
    "RetrievalPolicyEnforcer",
    "RetrievalQuery",
    "RetrievalResult",
    "RetrievedChunk",
    "SearchStrategy",
    "SemanticChunker",
    "SemanticSearchStrategy",
    "SimpleReranker",
    "SourceAttribution",
    "TextParser",
    "UnsupportedFormatError",
    "VectorStore",
    "create_chunker",
    "get_parser",
    "register_parser",
]
