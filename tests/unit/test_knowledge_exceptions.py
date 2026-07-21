from __future__ import annotations

from eaip.exceptions.base import ErrorCode
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


class TestKnowledgeExceptions:
    def test_knowledge_error_base(self) -> None:
        err = KnowledgeError("generic error")
        assert "generic error" in str(err)

    def test_document_parse_error(self) -> None:
        err = DocumentParseError("cannot parse")
        assert err.default_code is ErrorCode.VALIDATION_FAILED

    def test_chunking_error(self) -> None:
        err = ChunkingError("chunking failed")
        assert err.default_code is ErrorCode.UNKNOWN

    def test_embedding_error(self) -> None:
        err = EmbeddingError("embedding failed")
        assert err.default_code is ErrorCode.PROVIDER_UNAVAILABLE

    def test_collection_not_found(self) -> None:
        err = CollectionNotFoundError("collection not found")
        assert err.default_code is ErrorCode.NOT_FOUND

    def test_document_not_found(self) -> None:
        err = DocumentNotFoundError("doc not found")
        assert err.default_code is ErrorCode.NOT_FOUND

    def test_ingestion_error(self) -> None:
        IngestionError("ingestion failed")

    def test_retrieval_error(self) -> None:
        err = RetrievalError("retrieval failed")
        assert err.default_code is ErrorCode.UNKNOWN

    def test_unsupported_format(self) -> None:
        err = UnsupportedFormatError("unsupported")
        assert err.default_code is ErrorCode.VALIDATION_FAILED
