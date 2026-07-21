"""Exception hierarchy for cache invalidation."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class InvalidationError(EAIPError):
    """Base exception for cache invalidation errors."""

    default_code = ErrorCode.CACHE_ERROR


class TagNotFoundError(InvalidationError):
    """Raised when a cache tag is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "InvalidationError",
    "TagNotFoundError",
]
