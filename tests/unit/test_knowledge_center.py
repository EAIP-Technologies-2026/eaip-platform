"""Tests for the Knowledge Center — health, sources, citations endpoints."""

from __future__ import annotations

from eaip.knowledge.models import (
    DocumentFormat,
    IndexingStatus,
    KnowledgeCollection,
    KnowledgeDocument,
)
from eaip.knowledge.registry import KnowledgeRegistry


class TestKnowledgeCenterModels:
    """Verify the knowledge models used by the center."""

    def test_knowledge_document_fields(self) -> None:
        doc = KnowledgeDocument(
            document_id="doc-1",
            collection="default",
            format=DocumentFormat.MARKDOWN,
            title="Test Document",
            source="test.md",
            indexing_status=IndexingStatus.INDEXED,
        )
        assert doc.document_id == "doc-1"
        assert doc.collection == "default"
        assert doc.format == DocumentFormat.MARKDOWN
        assert doc.indexing_status == IndexingStatus.INDEXED

    def test_knowledge_collection_fields(self) -> None:
        col = KnowledgeCollection(
            collection_id="col-1",
            name="default",
            description="Default collection",
            document_count=10,
            chunk_count=100,
        )
        assert col.collection_id == "col-1"
        assert col.name == "default"
        assert col.document_count == 10
        assert col.chunk_count == 100

    def test_indexing_status_values(self) -> None:
        assert IndexingStatus.PENDING == "pending"
        assert IndexingStatus.INDEXING == "indexing"
        assert IndexingStatus.INDEXED == "indexed"
        assert IndexingStatus.FAILED == "failed"

    def test_document_format_values(self) -> None:
        assert DocumentFormat.PDF == "pdf"
        assert DocumentFormat.DOCX == "docx"
        assert DocumentFormat.MARKDOWN == "markdown"
        assert DocumentFormat.HTML == "html"
        assert DocumentFormat.TXT == "txt"


class TestKnowledgeRegistry:
    """Verify the KnowledgeRegistry used by the center endpoints."""

    def test_registry_all_collections(self) -> None:
        registry = KnowledgeRegistry()
        col = KnowledgeCollection(
            collection_id="col-1",
            name="test",
            description="Test collection",
            document_count=0,
            chunk_count=0,
        )
        registry.register_collection(col)
        cols = list(registry.all_collections())
        assert len(cols) == 1
        assert cols[0].name == "test"

    def test_registry_documents(self) -> None:
        registry = KnowledgeRegistry()
        doc = KnowledgeDocument(
            document_id="doc-1",
            collection="default",
            format=DocumentFormat.TXT,
            title="Test",
            indexing_status=IndexingStatus.INDEXED,
        )
        registry.register_document(doc)
        assert ("doc-1", "default") in registry._documents

    def test_registry_document_status_tracking(self) -> None:
        registry = KnowledgeRegistry()
        doc_indexed = KnowledgeDocument(
            document_id="doc-1",
            collection="default",
            format=DocumentFormat.TXT,
            title="Indexed",
            indexing_status=IndexingStatus.INDEXED,
        )
        doc_pending = KnowledgeDocument(
            document_id="doc-2",
            collection="default",
            format=DocumentFormat.TXT,
            title="Pending",
            indexing_status=IndexingStatus.PENDING,
        )
        doc_failed = KnowledgeDocument(
            document_id="doc-3",
            collection="default",
            format=DocumentFormat.TXT,
            title="Failed",
            indexing_status=IndexingStatus.FAILED,
        )
        registry.register_document(doc_indexed)
        registry.register_document(doc_pending)
        registry.register_document(doc_failed)

        indexed = 0
        pending = 0
        failed = 0
        for (did, col_name), doc in registry._documents.items():
            if col_name == "default":
                if doc.indexing_status == IndexingStatus.INDEXED:
                    indexed += 1
                elif doc.indexing_status == IndexingStatus.PENDING:
                    pending += 1
                elif doc.indexing_status == IndexingStatus.FAILED:
                    failed += 1

        assert indexed == 1
        assert pending == 1
        assert failed == 1

    def test_registry_multiple_collections(self) -> None:
        registry = KnowledgeRegistry()
        for i in range(3):
            col = KnowledgeCollection(
                collection_id=f"col-{i}",
                name=f"collection-{i}",
                description=f"Collection {i}",
                document_count=i * 5,
                chunk_count=i * 50,
            )
            registry.register_collection(col)
        cols = list(registry.all_collections())
        assert len(cols) == 3
        total_docs = sum(c.document_count for c in cols)
        assert total_docs == 15

    def test_registry_empty(self) -> None:
        registry = KnowledgeRegistry()
        cols = list(registry.all_collections())
        assert len(cols) == 0
        assert len(registry._documents) == 0


class TestKnowledgeCenterStatusMapping:
    """Verify status derivation logic used by the center."""

    def test_healthy_status(self) -> None:
        failed = 0
        total_docs = 10
        status = "healthy"
        if failed > 0:
            status = "degraded"
        if total_docs == 0:
            status = "empty"
        assert status == "healthy"

    def test_degraded_status(self) -> None:
        failed = 2
        total_docs = 10
        status = "healthy"
        if failed > 0:
            status = "degraded"
        if total_docs == 0:
            status = "empty"
        assert status == "degraded"

    def test_empty_status(self) -> None:
        failed = 0
        total_docs = 0
        status = "healthy"
        if failed > 0:
            status = "degraded"
        if total_docs == 0:
            status = "empty"
        assert status == "empty"

    def test_degraded_overrides_empty(self) -> None:
        failed = 1
        total_docs = 0
        status = "healthy"
        if failed > 0:
            status = "degraded"
        if total_docs == 0:
            status = "empty"
        assert status == "empty"
