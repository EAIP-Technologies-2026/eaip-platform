"""Exception hierarchy for diagnostic data collection."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DiagnosticError(EAIPError):
    """Base exception for diagnostic errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ReportNotFoundError(DiagnosticError):
    """Raised when a diagnostic report is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "DiagnosticError",
    "ReportNotFoundError",
]
