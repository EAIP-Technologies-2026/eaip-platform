"""Tests for the Semantic Indexing package."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.semantic_indexing.events import (
    IndexDocumentAdded,
    IndexDocumentRemoved,
    IndexDocumentUpdated,
    IndexMetricsCollected,
    IndexQueryExecuted,
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
    IndexQueryError,
    IndexRebuildError,
)
from eaip.semantic_indexing.models import (
    FieldType,
    IndexConfig,
    IndexDocument,
    IndexedField,
    IndexField,
    IndexMapping,
    IndexMetrics,
    IndexQuery,
    IndexQueryResult,
    IndexRebuildPlan,
    IndexStats,
    IndexStatus,
    SemanticIndex,
)
from eaip.semantic_indexing.service import SemanticIndexingService

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestFieldType:
    def test_values(self) -> None:
        assert FieldType.STRING.value == "string"
        assert FieldType.VECTOR.value == "vector"

    def test_members(self) -> None:
        assert len(FieldType) == 9


class TestIndexStatus:
    def test_values(self) -> None:
        assert IndexStatus.ACTIVE.value == "active"
        assert IndexStatus.REBUILDING.value == "rebuilding"

    def test_members(self) -> None:
        assert len(IndexStatus) == 7


class TestSemanticIndex:
    def test_defaults(self) -> None:
        config = IndexConfig(name="test")
        index = SemanticIndex(index_id="test", config=config)
        assert index.status == IndexStatus.CREATING
        assert index.document_count == 0
        assert index.size_bytes == 0
        assert index.last_rebuilt_at is None

    def test_frozen(self) -> None:
        config = IndexConfig(name="test")
        index = SemanticIndex(index_id="test", config=config)
        with pytest.raises(ValueError):
            index.status = IndexStatus.ACTIVE


class TestIndexConfig:
    def test_defaults(self) -> None:
        config = IndexConfig(name="test")
        assert config.name == "test"
        assert config.description == ""
        assert config.shard_count == 1
        assert config.replica_count == 1
        assert isinstance(config.created_at, datetime)

    def test_frozen(self) -> None:
        config = IndexConfig(name="test")
        with pytest.raises(ValueError):
            config.name = "other"


class TestIndexField:
    def test_defaults(self) -> None:
        field = IndexField(name="title")
        assert field.type == FieldType.STRING
        assert field.indexed is True
        assert field.searchable is True

    def test_frozen(self) -> None:
        field = IndexField(name="title")
        with pytest.raises(ValueError):
            field.name = "other"


class TestIndexMapping:
    def test_defaults(self) -> None:
        mapping = IndexMapping()
        assert mapping.fields == ()
        assert mapping.analyzers == ()

    def test_with_fields(self) -> None:
        field = IndexField(name="content", type=FieldType.TEXT)
        mapping = IndexMapping(fields=(field,))
        assert len(mapping.fields) == 1


class TestIndexDocument:
    def test_defaults(self) -> None:
        doc = IndexDocument(document_id="doc1", index_id="idx1")
        assert doc.score == 0.0
        assert doc.fields == ()

    def test_with_fields(self) -> None:
        field = IndexedField(name="title", value="hello")
        doc = IndexDocument(document_id="doc1", index_id="idx1", fields=(field,))
        assert len(doc.fields) == 1


class TestIndexQuery:
    def test_defaults(self) -> None:
        q = IndexQuery()
        assert q.query == ""
        assert q.top_k == 10
        assert q.offset == 0
        assert q.alpha == 1.0


class TestIndexQueryResult:
    def test_defaults(self) -> None:
        r = IndexQueryResult()
        assert r.total_hits == 0
        assert r.documents == ()
        assert r.duration_ms == 0.0


class TestIndexStats:
    def test_defaults(self) -> None:
        s = IndexStats(index_id="idx1")
        assert s.document_count == 0
        assert s.size_bytes == 0


class TestIndexMetrics:
    def test_defaults(self) -> None:
        m = IndexMetrics(index_id="idx1", operation="test")
        assert m.documents_processed == 0
        assert m.total_duration_ms == 0.0


class TestIndexRebuildPlan:
    def test_defaults(self) -> None:
        p = IndexRebuildPlan(index_id="idx1")
        assert p.reason == ""
        assert p.optimize_after_rebuild is True


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestSemanticIndexCreated:
    def test_event_type(self) -> None:
        e = SemanticIndexCreated(index_id="idx1", name="test", config={})
        assert e.event_type == "eaip.semantic_indexing.index.created"
        assert e.index_id == "idx1"

    def test_immutable(self) -> None:
        e = SemanticIndexCreated(index_id="idx1", name="test", config={})
        with pytest.raises(ValueError):
            e.index_id = "other"


class TestSemanticIndexDeleted:
    def test_event_type(self) -> None:
        e = SemanticIndexDeleted(index_id="idx1", name="test")
        assert e.event_type == "eaip.semantic_indexing.index.deleted"


class TestSemanticIndexRebuilt:
    def test_event_type(self) -> None:
        e = SemanticIndexRebuilt(index_id="idx1", name="test", document_count=5, duration_ms=10.0)
        assert e.event_type == "eaip.semantic_indexing.index.rebuilt"


class TestIndexDocumentAdded:
    def test_event_type(self) -> None:
        e = IndexDocumentAdded(document_id="doc1", index_id="idx1", field_count=3)
        assert e.event_type == "eaip.semantic_indexing.document.added"


class TestIndexQueryExecuted:
    def test_event_type(self) -> None:
        e = IndexQueryExecuted(index_id="idx1", query="test", result_count=2, duration_ms=1.0)
        assert e.event_type == "eaip.semantic_indexing.query.executed"


# ---------------------------------------------------------------------------
# Service — Index lifecycle
# ---------------------------------------------------------------------------


class TestCreateIndex:
    def test_create(self) -> None:
        svc = SemanticIndexingService()
        config = IndexConfig(name="My Index")
        index = svc.create_index(config)
        assert index.index_id == "my_index"
        assert index.status == IndexStatus.ACTIVE

    def test_duplicate_name_raises(self) -> None:
        svc = SemanticIndexingService()
        config = IndexConfig(name="My Index")
        svc.create_index(config)
        with pytest.raises(IndexConfigError):
            svc.create_index(config)

    def test_empty_name_raises(self) -> None:
        svc = SemanticIndexingService()
        config = IndexConfig(name="")
        with pytest.raises(IndexConfigError):
            svc.create_index(config)

    def test_emits_created_and_activated(self) -> None:
        svc = SemanticIndexingService()
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        config = IndexConfig(name="test")
        svc.create_index(config)
        types = [type(e).__name__ for e in events]
        assert "SemanticIndexCreated" in types
        assert "SemanticIndexActivated" in types


class TestGetIndex:
    def test_get_existing(self) -> None:
        svc = SemanticIndexingService()
        config = IndexConfig(name="test")
        svc.create_index(config)
        index = svc.get_index("test")
        assert index.index_id == "test"

    def test_get_missing_raises(self) -> None:
        svc = SemanticIndexingService()
        with pytest.raises(IndexNotFoundError):
            svc.get_index("nonexistent")


class TestUpdateIndex:
    def test_update(self) -> None:
        svc = SemanticIndexingService()
        config = IndexConfig(name="test")
        svc.create_index(config)
        updated = svc.update_index("test", description="new desc")
        assert updated.config.description == "new desc"

    def test_emits_updated(self) -> None:
        svc = SemanticIndexingService()
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        config = IndexConfig(name="test")
        svc.create_index(config)
        svc.update_index("test", description="new desc")
        assert any(isinstance(e, SemanticIndexUpdated) for e in events)


class TestDeleteIndex:
    def test_delete(self) -> None:
        svc = SemanticIndexingService()
        config = IndexConfig(name="test")
        svc.create_index(config)
        svc.delete_index("test")
        with pytest.raises(IndexNotFoundError):
            svc.get_index("test")

    def test_delete_missing_raises(self) -> None:
        svc = SemanticIndexingService()
        with pytest.raises(IndexNotFoundError):
            svc.delete_index("nonexistent")


class TestActivateDeactivate:
    def test_activate(self) -> None:
        svc = SemanticIndexingService()
        config = IndexConfig(name="test")
        svc.create_index(config)
        svc.deactivate_index("test")
        assert svc.get_index("test").status == IndexStatus.INACTIVE
        svc.activate_index("test")
        assert svc.get_index("test").status == IndexStatus.ACTIVE

    def test_deactivate_emits(self) -> None:
        svc = SemanticIndexingService()
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        config = IndexConfig(name="test")
        svc.create_index(config)
        svc.deactivate_index("test")
        assert any(isinstance(e, SemanticIndexDeactivated) for e in events)


class TestListIndexes:
    def test_empty(self) -> None:
        svc = SemanticIndexingService()
        assert svc.list_indexes() == []

    def test_multiple(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="a"))
        svc.create_index(IndexConfig(name="b"))
        assert len(svc.list_indexes()) == 2


# ---------------------------------------------------------------------------
# Service — Document management
# ---------------------------------------------------------------------------


class TestAddDocument:
    def test_add(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        result = svc.add_document("test", doc)
        assert result.document_id == "doc1"

    def test_add_duplicate_raises(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        with pytest.raises(IndexDocumentError):
            svc.add_document("test", doc)

    def test_emits_added(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        assert any(isinstance(e, IndexDocumentAdded) for e in events)

    def test_updates_document_count(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        assert svc.get_index("test").document_count == 1


class TestGetDocument:
    def test_get_existing(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        result = svc.get_document("test", "doc1")
        assert result.document_id == "doc1"

    def test_get_missing_raises(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        with pytest.raises(IndexDocumentError):
            svc.get_document("test", "nonexistent")


class TestUpdateDocument:
    def test_update(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        updated = svc.update_document("test", "doc1", score=0.5)
        assert updated.score == 0.5

    def test_emits_updated(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        svc.update_document("test", "doc1", score=0.5)
        assert any(isinstance(e, IndexDocumentUpdated) for e in events)


class TestRemoveDocument:
    def test_remove(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        svc.remove_document("test", "doc1")
        assert len(svc.list_documents("test")) == 0

    def test_remove_missing_raises(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        with pytest.raises(IndexDocumentError):
            svc.remove_document("test", "nonexistent")

    def test_emits_removed(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(document_id="doc1", index_id="test")
        svc.add_document("test", doc)
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        svc.remove_document("test", "doc1")
        assert any(isinstance(e, IndexDocumentRemoved) for e in events)


class TestListDocuments:
    def test_empty(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        assert svc.list_documents("test") == []

    def test_multiple(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        svc.add_document("test", IndexDocument(document_id="d1", index_id="test"))
        svc.add_document("test", IndexDocument(document_id="d2", index_id="test"))
        assert len(svc.list_documents("test")) == 2


# ---------------------------------------------------------------------------
# Service — Query
# ---------------------------------------------------------------------------


class TestQuery:
    def test_query(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        svc.add_document(
            "test",
            IndexDocument(document_id="d1", index_id="test"),
        )
        q = IndexQuery(index_id="test", query="hello")
        result = svc.query(q)
        assert result.total_hits == 1
        assert result.max_score == 1.0

    def test_query_empty_index(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        q = IndexQuery(index_id="test", query="hello")
        result = svc.query(q)
        assert result.total_hits == 0

    def test_emits_executed(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        q = IndexQuery(index_id="test", query="hello")
        svc.query(q)
        assert any(isinstance(e, IndexQueryExecuted) for e in events)


# ---------------------------------------------------------------------------
# Service — Stats
# ---------------------------------------------------------------------------


class TestStats:
    def test_stats(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        doc = IndexDocument(
            document_id="d1",
            index_id="test",
            fields=(IndexedField(name="title", value="hello"),),
        )
        svc.add_document("test", doc)
        stats = svc.get_stats("test")
        assert stats.document_count == 1
        assert stats.total_fields == 1


# ---------------------------------------------------------------------------
# Service — Rebuild
# ---------------------------------------------------------------------------


class TestRebuild:
    def test_rebuild(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        svc.add_document("test", IndexDocument(document_id="d1", index_id="test"))
        index = svc.rebuild_index("test")
        assert index.status == IndexStatus.ACTIVE

    def test_rebuild_emits(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        svc.rebuild_index("test")
        types = [type(e).__name__ for e in events]
        assert "IndexRebuildStarted" in types
        assert "IndexRebuildCompleted" in types
        assert "SemanticIndexRebuilt" in types

    def test_rebuild_with_plan(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        plan = IndexRebuildPlan(index_id="test", reason="schema change")
        index = svc.rebuild_index("test", plan=plan)
        assert index.status == IndexStatus.ACTIVE


# ---------------------------------------------------------------------------
# Service — Optimize
# ---------------------------------------------------------------------------


class TestOptimize:
    def test_optimize(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        index = svc.optimize_index("test")
        assert index.status == IndexStatus.ACTIVE

    def test_optimize_emits(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        svc.optimize_index("test")
        assert any(isinstance(e, SemanticIndexOptimized) for e in events)

    def test_optimize_inactive_raises(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        svc.deactivate_index("test")
        with pytest.raises(IndexOptimizationError):
            svc.optimize_index("test")


# ---------------------------------------------------------------------------
# Service — Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    def test_collect(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        svc.add_document("test", IndexDocument(document_id="d1", index_id="test"))
        metrics = svc.collect_metrics("test")
        assert metrics.index_id == "test"
        assert metrics.documents_processed == 1

    def test_emits_collected(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        events: list[object] = []
        svc.on(SemanticIndexingEvent, events.append)
        svc.collect_metrics("test")
        assert any(isinstance(e, IndexMetricsCollected) for e in events)


# ---------------------------------------------------------------------------
# Service — Mapping
# ---------------------------------------------------------------------------


class TestUpdateMapping:
    def test_update_mapping(self) -> None:
        svc = SemanticIndexingService()
        svc.create_index(IndexConfig(name="test"))
        index = svc.update_mapping("test")
        assert index is not None

    def test_update_mapping_missing_index(self) -> None:
        svc = SemanticIndexingService()
        with pytest.raises(IndexNotFoundError):
            svc.update_mapping("nonexistent")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_index_not_found(self) -> None:
        exc = IndexNotFoundError("test")
        assert "test" in str(exc)

    def test_index_config_error(self) -> None:
        exc = IndexConfigError("bad config")
        assert "bad config" in str(exc)

    def test_index_document_error(self) -> None:
        exc = IndexDocumentError("doc error")
        assert "doc error" in str(exc)

    def test_index_query_error(self) -> None:
        exc = IndexQueryError("query error")
        assert "query error" in str(exc)

    def test_index_rebuild_error(self) -> None:
        exc = IndexRebuildError("rebuild error")
        assert "rebuild error" in str(exc)

    def test_index_optimization_error(self) -> None:
        exc = IndexOptimizationError("opt error")
        assert "opt error" in str(exc)

    def test_index_mapping_error(self) -> None:
        exc = IndexMappingError("mapping error")
        assert "mapping error" in str(exc)
