"""Event-specific exception types."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class EventError(EAIPError):
    """Base for event-related failures."""

    default_code = ErrorCode.UNKNOWN


class EventPublishError(EventError):
    """Raised when event publishing fails after all retries."""

    default_code = ErrorCode.UNKNOWN


class EventHandlerError(EventError):
    """Raised when a handler fails and no error handler is configured."""

    default_code = ErrorCode.UNKNOWN


class EventRetryExhaustedError(EventError):
    """Raised when all retry attempts for an event have been exhausted."""

    default_code = ErrorCode.UNKNOWN


__all__ = [
    "EventError",
    "EventHandlerError",
    "EventPublishError",
    "EventRetryExhaustedError",
]
