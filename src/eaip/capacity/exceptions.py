"""Exception hierarchy for capacity analysis."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CapacityError(EAIPError):
    """Base exception for capacity analysis errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceNotFoundError(CapacityError):
    """Raised when a resource is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "CapacityError",
    "ResourceNotFoundError",
]
