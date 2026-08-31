"""Search index exception classes."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SearchIndexError(EAIPError):
    """Base exception for search index errors."""

    default_code = ErrorCode.UNKNOWN


class IndexNotFoundError(SearchIndexError):
    """Raised when a search index is not found."""

    default_code = ErrorCode.NOT_FOUND


class IndexBuildError(SearchIndexError):
    """Raised when an index build operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class CacheError(SearchIndexError):
    """Base exception for cache errors."""

    default_code = ErrorCode.CACHE_ERROR


class CacheNotFoundError(CacheError):
    """Raised when a cache entry is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "CacheError",
    "CacheNotFoundError",
    "IndexBuildError",
    "IndexNotFoundError",
    "SearchIndexError",
]
