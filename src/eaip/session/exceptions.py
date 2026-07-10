"""Session & context exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SessionError(EAIPError):
    """Base exception for session errors."""

    default_code = ErrorCode.UNKNOWN


class SessionNotFoundError(SessionError):
    """Raised when a requested session is not found."""

    default_code = ErrorCode.NOT_FOUND


class SessionExpiredError(SessionError):
    """Raised when an operation targets an expired session."""

    default_code = ErrorCode.POLICY_VIOLATION


class SessionLimitError(SessionError):
    """Raised when a session limit is exceeded."""

    default_code = ErrorCode.POLICY_VIOLATION


class ContextError(SessionError):
    """Raised when a context operation fails."""

    default_code = ErrorCode.UNKNOWN


__all__ = [
    "ContextError",
    "SessionError",
    "SessionExpiredError",
    "SessionLimitError",
    "SessionNotFoundError",
]
