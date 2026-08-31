"""Exception hierarchy for image tag management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class TagManagerError(EAIPError):
    """Base exception for image tag manager errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class TagNotFoundError(TagManagerError):
    """Raised when an image tag is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "TagManagerError",
    "TagNotFoundError",
]
