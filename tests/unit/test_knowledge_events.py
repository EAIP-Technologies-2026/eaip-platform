from __future__ import annotations

from eaip.knowledge.events import (
    CollectionCreated,
    CollectionDeleted,
    DocumentDeleted,
    DocumentIngested,
    KnowledgeQuery,
    RetrievalExecuted,
)


class TestKnowledgeEvents:
    def test_document_ingested(self) -> None:
        event = DocumentIngested(document_id="doc1", collection="default", chunk_count=5, duration_ms=100.0)
        assert event.event_type == "eaip.knowledge.document.ingested"
        assert event.document_id == "doc1"
        assert event.chunk_count == 5

    def test_document_deleted(self) -> None:
        event = DocumentDeleted(document_id="doc1", collection="default")
        assert event.event_type == "eaip.knowledge.document.deleted"

    def test_collection_created(self) -> None:
        event = CollectionCreated(collection_id="col:test", name="test", dimensions=384)
        assert event.event_type == "eaip.knowledge.collection.created"
        assert event.dimensions == 384

    def test_collection_deleted(self) -> None:
        event = CollectionDeleted(collection_id="col:test", name="test")
        assert event.event_type == "eaip.knowledge.collection.deleted"

    def test_retrieval_executed(self) -> None:
        event = RetrievalExecuted(query="test", collection="default", result_count=3, duration_ms=50.0)
        assert event.event_type == "eaip.knowledge.retrieval.executed"

    def test_knowledge_query(self) -> None:
        event = KnowledgeQuery(subject_id="user1", query="test", collection="default")
        assert event.event_type == "eaip.knowledge.query"
        assert event.subject_id == "user1"
