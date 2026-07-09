"""Knowledge Engine exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class KnowledgeError(EAIPError):
    """Base exception for Knowledge Engine errors."""

    default_code = ErrorCode.UNKNOWN


class KnowledgeEngineError(KnowledgeError):
    """Raised when the Knowledge Engine encounters an internal error."""

    default_code = ErrorCode.UNKNOWN


class DocumentParseError(KnowledgeError):
    """Raised when a document cannot be parsed."""

    default_code = ErrorCode.VALIDATION_FAILED


class ChunkingError(KnowledgeError):
    """Raised when document chunking fails."""

    default_code = ErrorCode.UNKNOWN


class EmbeddingError(KnowledgeError):
    """Raised when embedding generation fails."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class CollectionNotFoundError(KnowledgeError):
    """Raised when a knowledge collection does not exist."""

    default_code = ErrorCode.NOT_FOUND


class DocumentNotFoundError(KnowledgeError):
    """Raised when a document is not found."""

    default_code = ErrorCode.NOT_FOUND


class IngestionError(KnowledgeError):
    """Raised when document ingestion fails."""

    default_code = ErrorCode.UNKNOWN


class RetrievalError(KnowledgeError):
    """Raised when knowledge retrieval fails."""

    default_code = ErrorCode.UNKNOWN


class ProcessorRegistrationError(KnowledgeError):
    """Raised when a processor cannot be registered."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


class UnsupportedFormatError(KnowledgeError):
    """Raised when a document format is not supported."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "ChunkingError",
    "CollectionNotFoundError",
    "DocumentNotFoundError",
    "DocumentParseError",
    "EmbeddingError",
    "IngestionError",
    "KnowledgeEngineError",
    "KnowledgeError",
    "ProcessorRegistrationError",
    "RetrievalError",
    "UnsupportedFormatError",
]
