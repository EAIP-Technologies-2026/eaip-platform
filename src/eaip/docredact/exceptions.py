"""Exception hierarchy for document redaction."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class RedactionError(EAIPError):
    """Base exception for document redaction errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class RuleNotFoundError(RedactionError):
    """Raised when a redaction rule is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "RedactionError",
    "RuleNotFoundError",
]
