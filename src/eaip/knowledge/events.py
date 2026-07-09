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


__all__ = [
    "CollectionCreated",
    "CollectionDeleted",
    "DocumentDeleted",
    "DocumentIngested",
    "KnowledgeEngineEvent",
    "KnowledgeQuery",
    "RetrievalExecuted",
]
