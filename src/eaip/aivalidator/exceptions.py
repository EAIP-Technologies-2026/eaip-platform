"""Exception hierarchy for AI validation."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AIValidationError(EAIPError):
    """Base exception for AI validation errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class RuleNotFoundError(AIValidationError):
    """Raised when a validation rule is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "AIValidationError",
    "RuleNotFoundError",
]
