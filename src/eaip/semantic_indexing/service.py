"""Semantic Indexing service — index lifecycle, documents, query, rebuild, optimize."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from eaip.logging.context import get_logger
from eaip.semantic_indexing.events import (
    IndexDocumentAdded,
    IndexDocumentRemoved,
    IndexDocumentUpdated,
    IndexMetricsCollected,
    IndexQueryExecuted,
    IndexRebuildCompleted,
    IndexRebuildFailed,
    IndexRebuildStarted,
    SemanticIndexActivated,
    SemanticIndexCreated,
    SemanticIndexDeactivated,
    SemanticIndexDeleted,
    SemanticIndexingEvent,
    SemanticIndexOptimized,
    SemanticIndexRebuilt,
    SemanticIndexUpdated,
)
from eaip.semantic_indexing.exceptions import (
    IndexConfigError,
    IndexDocumentError,
    IndexMappingError,
    IndexNotFoundError,
    IndexOptimizationError,
    IndexRebuildError,
)
from eaip.semantic_indexing.models import (
    IndexConfig,
    IndexDocument,
    IndexMetrics,
    IndexQuery,
    IndexQueryResult,
    IndexRebuildPlan,
    IndexStats,
    IndexStatus,
    SemanticIndex,
)


class SemanticIndexingService:
    """Service for managing semantic indexes, documents, queries, rebuilds and optimization."""

    def __init__(self) -> None:
        """Initialize the service with empty in-memory storage."""
        self._indexes: dict[str, SemanticIndex] = {}
        self._documents: dict[str, dict[str, IndexDocument]] = {}
        self._event_handlers: list[Callable[[SemanticIndexingEvent], None]] = []
        self._log = get_logger("eaip.semantic_indexing.service")

    # -- Event handling -------------------------------------------------------

    def on(self, event_type: type, handler: Callable[[Any], None]) -> None:
        """Register an event handler.

        Args:
            event_type: The event type to listen for.
            handler: A callable that accepts the event.
        """

        def _wrapped(event: SemanticIndexingEvent) -> None:
            if isinstance(event, event_type):
                handler(event)

        self._event_handlers.append(_wrapped)

    def _emit(self, event: SemanticIndexingEvent) -> None:
        """Emit an event to all registered handlers.

        Args:
            event: The event to emit.
        """
        for handler in self._event_handlers:
            handler(event)

    # -- Index lifecycle ------------------------------------------------------

    def create_index(self, config: IndexConfig) -> SemanticIndex:
        """Create a new semantic index.

        Args:
            config: The index configuration.

        Returns:
            The created SemanticIndex.

        Raises:
            IndexConfigError: If the configuration is invalid.
        """
        if not config.name:
            raise IndexConfigError("Index name is required")

        index_id = config.name.lower().replace(" ", "_")
        if index_id in self._indexes:
            raise IndexConfigError(f"Index '{index_id}' already exists")

        index = SemanticIndex(
            index_id=index_id,
            config=config,
            status=IndexStatus.CREATING,
        )
        self._indexes[index_id] = index
        self._documents[index_id] = {}

        self._emit(
            SemanticIndexCreated(
                index_id=index_id,
                name=config.name,
                config=config.model_dump(),
            )
        )

        # Immediately activate
        index = index.model_copy(update={"status": IndexStatus.ACTIVE})
        self._indexes[index_id] = index

        self._emit(
            SemanticIndexActivated(
                index_id=index_id,
                name=config.name,
            )
        )

        return index

    def get_index(self, index_id: str) -> SemanticIndex:
        """Retrieve an index by ID.

        Args:
            index_id: The index identifier.

        Returns:
            The SemanticIndex.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        index = self._indexes.get(index_id)
        if index is None:
            raise IndexNotFoundError(f"Index '{index_id}' not found")
        return index

    def update_index(self, index_id: str, **changes: Any) -> SemanticIndex:
        """Update an index configuration.

        Args:
            index_id: The index identifier.
            **changes: Fields to update on the index config.

        Returns:
            The updated SemanticIndex.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        index = self.get_index(index_id)
        updated_config = index.config.model_copy(update=changes)
        updated_index = index.model_copy(
            update={"config": updated_config, "status": IndexStatus.ACTIVE}
        )
        self._indexes[index_id] = updated_index

        self._emit(
            SemanticIndexUpdated(
                index_id=index_id,
                name=index.config.name,
                changes=changes,
            )
        )

        return updated_index

    def delete_index(self, index_id: str) -> None:
        """Delete an index.

        Args:
            index_id: The index identifier.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        index = self.get_index(index_id)
        deleted = index.model_copy(update={"status": IndexStatus.DELETED})
        self._indexes[index_id] = deleted

        self._emit(
            SemanticIndexDeleted(
                index_id=index_id,
                name=index.config.name,
            )
        )

        self._documents.pop(index_id, None)
        self._indexes.pop(index_id, None)

    def list_indexes(self) -> list[SemanticIndex]:
        """List all indexes.

        Returns:
            A list of SemanticIndex instances.
        """
        return list(self._indexes.values())

    def activate_index(self, index_id: str) -> SemanticIndex:
        """Activate an index.

        Args:
            index_id: The index identifier.

        Returns:
            The activated SemanticIndex.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        index = self.get_index(index_id)
        updated = index.model_copy(update={"status": IndexStatus.ACTIVE})
        self._indexes[index_id] = updated

        self._emit(
            SemanticIndexActivated(
                index_id=index_id,
                name=index.config.name,
            )
        )

        return updated

    def deactivate_index(self, index_id: str) -> SemanticIndex:
        """Deactivate an index.

        Args:
            index_id: The index identifier.

        Returns:
            The deactivated SemanticIndex.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        index = self.get_index(index_id)
        updated = index.model_copy(update={"status": IndexStatus.INACTIVE})
        self._indexes[index_id] = updated

        self._emit(
            SemanticIndexDeactivated(
                index_id=index_id,
                name=index.config.name,
            )
        )

        return updated

    # -- Document management --------------------------------------------------

    def add_document(self, index_id: str, document: IndexDocument) -> IndexDocument:
        """Add a document to an index.

        Args:
            index_id: The index identifier.
            document: The document to add.

        Returns:
            The added IndexDocument.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexDocumentError: If the document cannot be added.
        """
        self.get_index(index_id)

        if document.document_id in self._documents.get(index_id, {}):
            raise IndexDocumentError(
                f"Document '{document.document_id}' already exists in index '{index_id}'"
            )

        self._documents.setdefault(index_id, {})[document.document_id] = document

        index = self._indexes[index_id]
        self._indexes[index_id] = index.model_copy(
            update={"document_count": index.document_count + 1}
        )

        self._emit(
            IndexDocumentAdded(
                document_id=document.document_id,
                index_id=index_id,
                field_count=len(document.fields),
            )
        )

        return document

    def get_document(self, index_id: str, document_id: str) -> IndexDocument:
        """Retrieve a document from an index.

        Args:
            index_id: The index identifier.
            document_id: The document identifier.

        Returns:
            The IndexDocument.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexDocumentError: If the document is not found.
        """
        self.get_index(index_id)
        docs = self._documents.get(index_id, {})
        doc = docs.get(document_id)
        if doc is None:
            raise IndexDocumentError(f"Document '{document_id}' not found in index '{index_id}'")
        return doc

    def update_document(self, index_id: str, document_id: str, **fields: Any) -> IndexDocument:
        """Update a document in an index.

        Args:
            index_id: The index identifier.
            document_id: The document identifier.
            **fields: Field values to update.

        Returns:
            The updated IndexDocument.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexDocumentError: If the document is not found.
        """
        existing = self.get_document(index_id, document_id)
        updated = existing.model_copy(update=fields)
        self._documents[index_id][document_id] = updated

        self._emit(
            IndexDocumentUpdated(
                document_id=document_id,
                index_id=index_id,
                field_count=len(updated.fields),
            )
        )

        return updated

    def remove_document(self, index_id: str, document_id: str) -> None:
        """Remove a document from an index.

        Args:
            index_id: The index identifier.
            document_id: The document identifier.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexDocumentError: If the document is not found.
        """
        self.get_document(index_id, document_id)
        del self._documents[index_id][document_id]

        index = self._indexes[index_id]
        self._indexes[index_id] = index.model_copy(
            update={"document_count": max(0, index.document_count - 1)}
        )

        self._emit(
            IndexDocumentRemoved(
                document_id=document_id,
                index_id=index_id,
            )
        )

    def list_documents(self, index_id: str) -> list[IndexDocument]:
        """List all documents in an index.

        Args:
            index_id: The index identifier.

        Returns:
            A list of IndexDocument instances.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        self.get_index(index_id)
        return list(self._documents.get(index_id, {}).values())

    # -- Query ----------------------------------------------------------------

    def query(self, index_query: IndexQuery) -> IndexQueryResult:
        """Execute a query against an index.

        Args:
            index_query: The query to execute.

        Returns:
            An IndexQueryResult.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexQueryError: If the query fails.
        """
        self.get_index(index_query.index_id)

        docs = list(self._documents.get(index_query.index_id, {}).values())
        matched = docs[: index_query.top_k]

        result = IndexQueryResult(
            query=index_query.query,
            index_id=index_query.index_id,
            documents=tuple(matched),
            total_hits=len(matched),
            duration_ms=0.0,
            max_score=1.0 if matched else 0.0,
        )

        self._emit(
            IndexQueryExecuted(
                index_id=index_query.index_id,
                query=index_query.query,
                result_count=len(matched),
                duration_ms=result.duration_ms,
            )
        )

        return result

    # -- Stats ----------------------------------------------------------------

    def get_stats(self, index_id: str) -> IndexStats:
        """Get statistics for an index.

        Args:
            index_id: The index identifier.

        Returns:
            An IndexStats instance.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        index = self.get_index(index_id)
        docs = self._documents.get(index_id, {})
        field_count = sum(len(d.fields) for d in docs.values()) if docs else 0

        return IndexStats(
            index_id=index_id,
            document_count=len(docs),
            total_fields=field_count,
            indexed_fields=field_count,
            size_bytes=index.size_bytes,
            segment_count=max(1, len(docs) // 100) if docs else 0,
            deleted_document_count=0,
        )

    # -- Rebuild --------------------------------------------------------------

    def rebuild_index(self, index_id: str, plan: IndexRebuildPlan | None = None) -> SemanticIndex:
        """Rebuild an index.

        Args:
            index_id: The index identifier.
            plan: Optional rebuild plan.

        Returns:
            The rebuilt SemanticIndex.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexRebuildError: If the rebuild fails.
        """
        index = self.get_index(index_id)

        reason = plan.reason if plan else "manual"
        self._emit(
            IndexRebuildStarted(
                index_id=index_id,
                name=index.config.name,
                reason=reason,
            )
        )

        rebuilding = index.model_copy(update={"status": IndexStatus.REBUILDING})
        self._indexes[index_id] = rebuilding

        try:
            docs = self._documents.get(index_id, {})
            doc_count = len(docs)

            rebuilt = rebuilding.model_copy(
                update={
                    "status": IndexStatus.ACTIVE,
                    "document_count": doc_count,
                    "last_rebuilt_at": None,
                }
            )
            self._indexes[index_id] = rebuilt

            self._emit(
                IndexRebuildCompleted(
                    index_id=index_id,
                    name=index.config.name,
                    document_count=doc_count,
                    duration_ms=0.0,
                )
            )

            self._emit(
                SemanticIndexRebuilt(
                    index_id=index_id,
                    name=index.config.name,
                    document_count=doc_count,
                    duration_ms=0.0,
                )
            )
        except Exception as exc:
            failed = rebuilding.model_copy(update={"status": IndexStatus.FAILED})
            self._indexes[index_id] = failed

            self._emit(
                IndexRebuildFailed(
                    index_id=index_id,
                    name=index.config.name,
                    error=str(exc),
                    duration_ms=0.0,
                )
            )
            raise IndexRebuildError(f"Rebuild failed for index '{index_id}'") from exc

        return self._indexes[index_id]

    # -- Optimize -------------------------------------------------------------

    def optimize_index(self, index_id: str) -> SemanticIndex:
        """Optimize an index (merge segments, reclaim space).

        Args:
            index_id: The index identifier.

        Returns:
            The optimized SemanticIndex.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexOptimizationError: If the optimization fails.
        """
        index = self.get_index(index_id)

        if index.status != IndexStatus.ACTIVE:
            raise IndexOptimizationError(
                f"Cannot optimize index '{index_id}' in status '{index.status.value}'"
            )

        optimizing = index.model_copy(update={"status": IndexStatus.OPTIMIZING})
        self._indexes[index_id] = optimizing

        optimized = optimizing.model_copy(
            update={
                "status": IndexStatus.ACTIVE,
                "last_optimized_at": None,
            }
        )
        self._indexes[index_id] = optimized

        self._emit(
            SemanticIndexOptimized(
                index_id=index_id,
                name=index.config.name,
                segments_merged=1,
                duration_ms=0.0,
            )
        )

        return optimized

    # -- Metrics --------------------------------------------------------------

    def collect_metrics(self, index_id: str) -> IndexMetrics:
        """Collect metrics for an index.

        Args:
            index_id: The index identifier.

        Returns:
            An IndexMetrics instance.

        Raises:
            IndexNotFoundError: If the index does not exist.
        """
        self.get_index(index_id)
        docs = self._documents.get(index_id, {})

        metrics = IndexMetrics(
            index_id=index_id,
            operation="collect",
            documents_processed=len(docs),
            documents_failed=0,
            total_duration_ms=0.0,
            avg_document_time_ms=0.0,
            throughput_dps=0.0,
            memory_bytes=0,
        )

        self._emit(
            IndexMetricsCollected(
                index_id=index_id,
                operation="collect",
                documents_processed=len(docs),
                documents_failed=0,
                total_duration_ms=0.0,
            )
        )

        return metrics

    # -- Mapping --------------------------------------------------------------

    def update_mapping(self, index_id: str, **mapping_changes: Any) -> SemanticIndex:
        """Update the mapping of an index.

        Args:
            index_id: The index identifier.
            **mapping_changes: Mapping field updates.

        Returns:
            The updated SemanticIndex.

        Raises:
            IndexNotFoundError: If the index does not exist.
            IndexMappingError: If the mapping update fails.
        """
        index = self.get_index(index_id)

        try:
            updated_config = index.config.model_copy(update={"mapping": mapping_changes})
            updated = index.model_copy(update={"config": updated_config})
            self._indexes[index_id] = updated
        except Exception as exc:
            raise IndexMappingError(f"Failed to update mapping for index '{index_id}'") from exc

        return updated


__all__ = ["SemanticIndexingService"]
