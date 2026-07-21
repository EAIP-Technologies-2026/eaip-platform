"""Semantic Indexing domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class SemanticIndexingEvent(DomainEvent):
    """Base event for all Semantic Indexing events."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.event"


class SemanticIndexCreated(SemanticIndexingEvent):
    """Published when a semantic index is created."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.index.created"
    index_id: str
    name: str
    config: dict[str, Any]


class SemanticIndexUpdated(SemanticIndexingEvent):
    """Published when a semantic index configuration is updated."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.index.updated"
    index_id: str
    name: str
    changes: dict[str, Any]


class SemanticIndexDeleted(SemanticIndexingEvent):
    """Published when a semantic index is deleted."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.index.deleted"
    index_id: str
    name: str


class SemanticIndexActivated(SemanticIndexingEvent):
    """Published when a semantic index is activated."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.index.activated"
    index_id: str
    name: str


class SemanticIndexDeactivated(SemanticIndexingEvent):
    """Published when a semantic index is deactivated."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.index.deactivated"
    index_id: str
    name: str


class SemanticIndexRebuilt(SemanticIndexingEvent):
    """Published when a semantic index has been rebuilt."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.index.rebuilt"
    index_id: str
    name: str
    document_count: int
    duration_ms: float


class SemanticIndexOptimized(SemanticIndexingEvent):
    """Published when a semantic index has been optimized."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.index.optimized"
    index_id: str
    name: str
    segments_merged: int
    duration_ms: float


class IndexDocumentAdded(SemanticIndexingEvent):
    """Published when a document is added to an index."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.document.added"
    document_id: str
    index_id: str
    field_count: int


class IndexDocumentUpdated(SemanticIndexingEvent):
    """Published when a document in an index is updated."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.document.updated"
    document_id: str
    index_id: str
    field_count: int


class IndexDocumentRemoved(SemanticIndexingEvent):
    """Published when a document is removed from an index."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.document.removed"
    document_id: str
    index_id: str


class IndexQueryExecuted(SemanticIndexingEvent):
    """Published after a query is executed against an index."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.query.executed"
    index_id: str
    query: str
    result_count: int
    duration_ms: float


class IndexMetricsCollected(SemanticIndexingEvent):
    """Published when index metrics are collected."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.metrics.collected"
    index_id: str
    operation: str
    documents_processed: int
    documents_failed: int
    total_duration_ms: float


class IndexRebuildStarted(SemanticIndexingEvent):
    """Published when an index rebuild starts."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.rebuild.started"
    index_id: str
    name: str
    reason: str


class IndexRebuildCompleted(SemanticIndexingEvent):
    """Published when an index rebuild completes successfully."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.rebuild.completed"
    index_id: str
    name: str
    document_count: int
    duration_ms: float


class IndexRebuildFailed(SemanticIndexingEvent):
    """Published when an index rebuild fails."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.rebuild.failed"
    index_id: str
    name: str
    error: str
    duration_ms: float


class IndexConfigUpdated(SemanticIndexingEvent):
    """Published when index configuration is updated."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.config.updated"
    index_id: str
    name: str
    changes: dict[str, Any]


class IndexMappingChanged(SemanticIndexingEvent):
    """Published when the index mapping is changed."""

    event_type: ClassVar[str] = "eaip.semantic_indexing.mapping.changed"
    index_id: str
    name: str
    added_fields: tuple[str, ...] = ()
    removed_fields: tuple[str, ...] = ()
    modified_fields: tuple[str, ...] = ()


__all__ = [
    "IndexConfigUpdated",
    "IndexDocumentAdded",
    "IndexDocumentRemoved",
    "IndexDocumentUpdated",
    "IndexMappingChanged",
    "IndexMetricsCollected",
    "IndexQueryExecuted",
    "IndexRebuildCompleted",
    "IndexRebuildFailed",
    "IndexRebuildStarted",
    "SemanticIndexActivated",
    "SemanticIndexCreated",
    "SemanticIndexDeactivated",
    "SemanticIndexDeleted",
    "SemanticIndexOptimized",
    "SemanticIndexRebuilt",
    "SemanticIndexUpdated",
    "SemanticIndexingEvent",
]
