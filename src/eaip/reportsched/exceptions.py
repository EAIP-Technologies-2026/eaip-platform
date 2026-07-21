"""Exception hierarchy for report scheduling."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SchedulerError(EAIPError):
    """Base exception for scheduler errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ReportNotFoundError(SchedulerError):
    """Raised when a report definition is not found."""

    default_code = ErrorCode.NOT_FOUND


class ReportGenerationError(SchedulerError):
    """Raised when report generation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "ReportGenerationError",
    "ReportNotFoundError",
    "SchedulerError",
]
