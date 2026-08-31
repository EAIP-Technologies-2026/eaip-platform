"""Exception hierarchy for dependency scanning."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ScanError(EAIPError):
    """Base exception for dependency scanning errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class TargetNotFoundError(ScanError):
    """Raised when a scan target is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "ScanError",
    "TargetNotFoundError",
]
