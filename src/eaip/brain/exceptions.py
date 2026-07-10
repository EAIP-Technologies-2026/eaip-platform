"""Enterprise Brain exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class BrainError(EAIPError):
    """Base exception for Enterprise Brain errors."""

    default_code = ErrorCode.UNKNOWN


class BrainQueryError(BrainError):
    """Raised when a brain query fails."""

    default_code = ErrorCode.UNKNOWN


class BrainSourceUnavailableError(BrainError):
    """Raised when a brain source is unavailable."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class BrainAccessDeniedError(BrainError):
    """Raised when a brain query is denied by access control."""

    default_code = ErrorCode.POLICY_VIOLATION


__all__ = [
    "BrainAccessDeniedError",
    "BrainError",
    "BrainQueryError",
    "BrainSourceUnavailableError",
]
