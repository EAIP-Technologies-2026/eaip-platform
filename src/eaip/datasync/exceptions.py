"""Exception hierarchy for data synchronization."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SyncError(EAIPError):
    """Base exception for data synchronization errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class SyncJobNotFoundError(SyncError):
    """Raised when a sync job is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "SyncError",
    "SyncJobNotFoundError",
]
