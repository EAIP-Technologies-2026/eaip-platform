"""Memory Engine exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class MemoryError(EAIPError):
    """Base exception for Memory Engine errors."""

    default_code = ErrorCode.UNKNOWN


class MemoryEngineError(MemoryError):
    """Raised when the Memory Engine encounters an internal error."""

    default_code = ErrorCode.UNKNOWN


class MemoryNotFoundError(MemoryError):
    """Raised when a memory item is not found."""

    default_code = ErrorCode.NOT_FOUND


class MemoryStoreError(MemoryError):
    """Raised when a memory store operation fails."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class MemoryValidationError(MemoryError):
    """Raised when memory data validation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


class MemoryIndexingError(MemoryError):
    """Raised when memory indexing fails."""

    default_code = ErrorCode.UNKNOWN


class MemoryRetrievalError(MemoryError):
    """Raised when memory retrieval fails."""

    default_code = ErrorCode.UNKNOWN


class MemoryConsolidationError(MemoryError):
    """Raised when memory consolidation fails."""

    default_code = ErrorCode.UNKNOWN


class MemorySummarizationError(MemoryError):
    """Raised when memory summarization fails."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class MemoryExpiredError(MemoryError):
    """Raised when attempting to access an expired memory."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "MemoryConsolidationError",
    "MemoryEngineError",
    "MemoryError",
    "MemoryExpiredError",
    "MemoryIndexingError",
    "MemoryNotFoundError",
    "MemoryRetrievalError",
    "MemoryStoreError",
    "MemorySummarizationError",
    "MemoryValidationError",
]
