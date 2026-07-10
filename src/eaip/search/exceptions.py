"""Search system exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SearchError(EAIPError):
    """Base exception for search system errors."""

    default_code = ErrorCode.UNKNOWN


class SearchQueryError(SearchError):
    """Raised when a search query is invalid."""

    default_code = ErrorCode.VALIDATION_FAILED


class ProviderNotFoundError(SearchError):
    """Raised when a search provider is not found."""

    default_code = ErrorCode.PROVIDER_NOT_FOUND


class ProviderSearchError(SearchError):
    """Raised when a search provider encounters an error during search."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


__all__ = [
    "ProviderNotFoundError",
    "ProviderSearchError",
    "SearchError",
    "SearchQueryError",
]
