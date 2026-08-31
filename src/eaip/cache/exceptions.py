"""Cache-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CacheError(EAIPError):
    """Base exception for all cache-related errors."""

    default_code: ErrorCode = ErrorCode.UNKNOWN

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        super().__init__(message)


class CacheMissError(CacheError):
    """Raised when a requested key is not found in the cache."""

    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        super().__init__(message)


class CacheStorageError(CacheError):
    """Raised when a storage operation fails in the cache backend."""

    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        super().__init__(message)
