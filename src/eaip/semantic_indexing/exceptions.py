"""Semantic Indexing exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SemanticIndexingError(EAIPError):
    """Base exception for Semantic Indexing errors."""

    default_code = ErrorCode.UNKNOWN


class IndexNotFoundError(SemanticIndexingError):
    """Raised when a semantic index does not exist."""

    default_code = ErrorCode.NOT_FOUND


class IndexConfigError(SemanticIndexingError):
    """Raised when index configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class IndexDocumentError(SemanticIndexingError):
    """Raised when a document operation fails."""

    default_code = ErrorCode.UNKNOWN


class IndexQueryError(SemanticIndexingError):
    """Raised when a query execution fails."""

    default_code = ErrorCode.UNKNOWN


class IndexRebuildError(SemanticIndexingError):
    """Raised when an index rebuild operation fails."""

    default_code = ErrorCode.UNKNOWN


class IndexOptimizationError(SemanticIndexingError):
    """Raised when an index optimization operation fails."""

    default_code = ErrorCode.UNKNOWN


class IndexMappingError(SemanticIndexingError):
    """Raised when an index mapping operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "IndexConfigError",
    "IndexDocumentError",
    "IndexMappingError",
    "IndexNotFoundError",
    "IndexOptimizationError",
    "IndexQueryError",
    "IndexRebuildError",
    "SemanticIndexingError",
]
