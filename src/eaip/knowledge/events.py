"""Knowledge Engine domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class KnowledgeEngineEvent(DomainEvent):
    """Base event for all Knowledge Engine events."""

    event_type: ClassVar[str] = "eaip.knowledge.event"


class DocumentIngested(KnowledgeEngineEvent):
    """Published when a document has been ingested."""

    event_type: ClassVar[str] = "eaip.knowledge.document.ingested"
    document_id: str
    collection: str
    chunk_count: int
    duration_ms: float


class DocumentDeleted(KnowledgeEngineEvent):
    """Published when a document has been deleted."""

    event_type: ClassVar[str] = "eaip.knowledge.document.deleted"
    document_id: str
    collection: str


class CollectionCreated(KnowledgeEngineEvent):
    """Published when a knowledge collection has been created."""

    event_type: ClassVar[str] = "eaip.knowledge.collection.created"
    collection_id: str
    name: str
    dimensions: int


class CollectionDeleted(KnowledgeEngineEvent):
    """Published when a knowledge collection has been deleted."""

    event_type: ClassVar[str] = "eaip.knowledge.collection.deleted"
    collection_id: str
    name: str


class RetrievalExecuted(KnowledgeEngineEvent):
    """Published after a retrieval query is executed."""

    event_type: ClassVar[str] = "eaip.knowledge.retrieval.executed"
    query: str
    collection: str
    result_count: int
    duration_ms: float


class KnowledgeQuery(KnowledgeEngineEvent):
    """Published when a knowledge query is made (for audit)."""

    event_type: ClassVar[str] = "eaip.knowledge.query"
    subject_id: str = ""
    action: str = "query"
    resource: str = ""
    query: str = ""
    collection: str = ""


class HybridSearchExecuted(KnowledgeEngineEvent):
    """Published after a hybrid (semantic + keyword) search is executed."""

    event_type: ClassVar[str] = "eaip.knowledge.hybrid_search.executed"
    query: str
    collection: str
    result_count: int
    duration_ms: float
    alpha: float = 0.5


class FederatedSearchExecuted(KnowledgeEngineEvent):
    """Published after a federated search across multiple sources."""

    event_type: ClassVar[str] = "eaip.knowledge.federated_search.executed"
    query: str
    sources: tuple[str, ...] = ()
    result_count: int
    duration_ms: float


# ── Pipeline stage events ──────────────────────────────────────────


class KnowledgeUploaded(KnowledgeEngineEvent):
    """Published when a document is uploaded to the ingestion pipeline."""

    event_type: ClassVar[str] = "eaip.knowledge.uploaded"
    document_id: str
    collection: str
    size_bytes: int
    format: str


class ChunkingCompleted(KnowledgeEngineEvent):
    """Published after document chunking completes."""

    event_type: ClassVar[str] = "eaip.knowledge.chunking.completed"
    document_id: str
    chunk_count: int
    duration_ms: float


class EmbeddingCreated(KnowledgeEngineEvent):
    """Published when embeddings are generated for document chunks."""

    event_type: ClassVar[str] = "eaip.knowledge.embedding.created"
    document_id: str
    chunk_count: int
    dimensions: int
    duration_ms: float


class KnowledgeIndexed(KnowledgeEngineEvent):
    """Published when a document is fully indexed in the vector store."""

    event_type: ClassVar[str] = "eaip.knowledge.indexed"
    document_id: str
    collection: str
    chunk_count: int
    duration_ms: float


class SearchExecuted(KnowledgeEngineEvent):
    """Published after any knowledge search (semantic, hybrid, keyword)."""

    event_type: ClassVar[str] = "eaip.knowledge.search.executed"
    query: str
    collection: str
    search_type: str = "semantic"
    result_count: int
    duration_ms: float


class VectorStoreCleared(KnowledgeEngineEvent):
    """Published when a vector store collection is cleared."""

    event_type: ClassVar[str] = "eaip.knowledge.vector_store.cleared"
    collection: str


__all__ = [
    "ChunkingCompleted",
    "CollectionCreated",
    "CollectionDeleted",
    "DocumentDeleted",
    "DocumentIngested",
    "EmbeddingCreated",
    "FederatedSearchExecuted",
    "HybridSearchExecuted",
    "KnowledgeEngineEvent",
    "KnowledgeIndexed",
    "KnowledgeQuery",
    "KnowledgeUploaded",
    "RetrievalExecuted",
    "SearchExecuted",
    "VectorStoreCleared",
]
