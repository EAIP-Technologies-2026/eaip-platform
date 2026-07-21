"""Exception hierarchy for incident communication."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CommError(EAIPError):
    """Base exception for communication errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class IncidentNotFoundError(CommError):
    """Raised when an incident is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "CommError",
    "IncidentNotFoundError",
]
