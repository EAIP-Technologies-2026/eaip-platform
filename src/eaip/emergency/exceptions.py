"""Exception hierarchy for emergency access management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class EmergencyError(EAIPError):
    """Base exception for emergency access errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class RequestNotFoundError(EmergencyError):
    """Raised when an emergency request is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "EmergencyError",
    "RequestNotFoundError",
]
