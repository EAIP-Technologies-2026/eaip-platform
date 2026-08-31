"""Exception hierarchy for feedback collection."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class FeedbackError(EAIPError):
    """Base exception for feedback collection errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class FeedbackNotFoundError(FeedbackError):
    """Raised when a feedback item is not found."""

    default_code = ErrorCode.NOT_FOUND


class FeedbackDuplicateError(FeedbackError):
    """Raised when a duplicate feedback submission is detected."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


__all__ = [
    "FeedbackDuplicateError",
    "FeedbackError",
    "FeedbackNotFoundError",
]
