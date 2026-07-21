"""Exception hierarchy for alert correlation."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CorrelationError(EAIPError):
    """Base exception for alert correlation errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class RuleNotFoundError(CorrelationError):
    """Raised when a correlation rule is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "CorrelationError",
    "RuleNotFoundError",
]
