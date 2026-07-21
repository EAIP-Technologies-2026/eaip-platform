from __future__ import annotations

from eaip.knowledge.models import (
    DocumentChunk,
    DocumentFormat,
    KnowledgeCollection,
    KnowledgeDocument,
)
from eaip.knowledge.registry import KnowledgeRegistry


class _Col:
    @staticmethod
    def make(name: str = "default") -> KnowledgeCollection:
        return KnowledgeCollection(collection_id=f"col:{name}", name=name)


class _Doc:
    @staticmethod
    def make(doc_id: str = "doc1", col: str = "default") -> KnowledgeDocument:
        return KnowledgeDocument(document_id=doc_id, collection=col, format=DocumentFormat.TXT)


class TestKnowledgeRegistry:
    def test_register_collection(self) -> None:
        reg = KnowledgeRegistry()
        col = _Col.make("test")
        reg.register_collection(col)
        assert reg.has_collection("test")
        assert reg.get_collection("test") is col

    def test_register_duplicate_collection(self) -> None:
        reg = KnowledgeRegistry()
        reg.register_collection(_Col.make("dup"))
        reg.register_collection(_Col.make("dup"), replace=True)
        assert reg.collection_count() == 1

    def test_unregister_collection(self) -> None:
        reg = KnowledgeRegistry()
        reg.register_collection(_Col.make("del"))
        assert reg.unregister_collection("del")
        assert not reg.has_collection("del")

    def test_all_collections(self) -> None:
        reg = KnowledgeRegistry()
        reg.register_collection(_Col.make("a"))
        reg.register_collection(_Col.make("b"))
        assert len(reg.all_collections()) == 2

    def test_register_document(self) -> None:
        reg = KnowledgeRegistry()
        doc = _Doc.make("d1", "default")
        reg.register_document(doc)
        assert reg.has_document("d1", "default")
        assert reg.get_document("d1", "default") is doc

    def test_unregister_document(self) -> None:
        reg = KnowledgeRegistry()
        reg.register_document(_Doc.make("d1", "default"))
        assert reg.unregister_document("d1", "default")
        assert not reg.has_document("d1", "default")

    def test_all_documents_filtered_by_collection(self) -> None:
        reg = KnowledgeRegistry()
        reg.register_document(_Doc.make("d1", "col1"))
        reg.register_document(_Doc.make("d2", "col2"))
        reg.register_document(_Doc.make("d3", "col1"))
        assert len(reg.all_documents("col1")) == 2
        assert len(reg.all_documents("col2")) == 1

    def test_document_count(self) -> None:
        reg = KnowledgeRegistry()
        assert reg.document_count() == 0
        reg.register_document(_Doc.make("d1", "default"))
        assert reg.document_count() == 1
        assert reg.document_count("default") == 1
        assert reg.document_count("other") == 0

    def test_register_chunks(self) -> None:
        reg = KnowledgeRegistry()
        chunks = [
            DocumentChunk(chunk_id="c1", document_id="d1", collection="default", content="a"),
            DocumentChunk(chunk_id="c2", document_id="d1", collection="default", content="b"),
        ]
        reg.register_chunks(chunks)
        retrieved = reg.get_document_chunks("d1", "default")
        assert len(retrieved) == 2

    def test_clear(self) -> None:
        reg = KnowledgeRegistry()
        reg.register_collection(_Col.make("col1"))
        reg.register_document(_Doc.make("d1"))
        reg.clear()
        assert reg.collection_count() == 0
        assert reg.document_count() == 0

    def test_doc_key_uniqueness(self) -> None:
        reg = KnowledgeRegistry()
        d1 = _Doc.make("same_id", "col_a")
        d2 = _Doc.make("same_id", "col_b")
        reg.register_document(d1)
        reg.register_document(d2)
        assert reg.document_count() == 2
        assert reg.get_document("same_id", "col_a") is d1
        assert reg.get_document("same_id", "col_b") is d2
