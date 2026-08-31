"""Queue-specific exception types."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class QueueError(EAIPError):
    """Base for queue-related failures."""

    default_code = ErrorCode.UNKNOWN


class QueueFullError(QueueError):
    """Raised when trying to enqueue into a full queue."""

    default_code = ErrorCode.RATE_LIMITED


class QueueEmptyError(QueueError):
    """Raised when trying to dequeue from an empty queue."""

    default_code = ErrorCode.NOT_FOUND


class QueueClosedError(QueueError):
    """Raised when operating on a closed queue."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


__all__ = [
    "QueueClosedError",
    "QueueEmptyError",
    "QueueError",
    "QueueFullError",
]
