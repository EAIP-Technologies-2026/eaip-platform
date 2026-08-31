"""Exception hierarchy for external identity mapping."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class MappingError(EAIPError):
    """Base exception for identity mapping errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class MappingNotFoundError(MappingError):
    """Raised when an identity mapping is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "MappingError",
    "MappingNotFoundError",
]
