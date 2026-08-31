"""Exception hierarchy for idle resource notification."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class NotifierError(EAIPError):
    """Base exception for notifier errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceNotFoundError(NotifierError):
    """Raised when a resource is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "NotifierError",
    "ResourceNotFoundError",
]
