"""Exception hierarchy for batch job scheduling."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class BatchJobError(EAIPError):
    """Base exception for batch job errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class BatchJobNotFoundError(BatchJobError):
    """Raised when a batch job is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "BatchJobError",
    "BatchJobNotFoundError",
]
