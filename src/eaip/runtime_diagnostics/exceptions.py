"""Exception hierarchy for runtime diagnostics."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class RuntimeDiagnosticsError(EAIPError):
    """Base exception for runtime diagnostics errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class DiagnosticsConfigError(RuntimeDiagnosticsError):
    """Raised when runtime diagnostics configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class DiagnosticsProbeError(RuntimeDiagnosticsError):
    """Raised when a diagnostics probe operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class DiagnosticsCheckError(RuntimeDiagnosticsError):
    """Raised when a diagnostics check operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class DiagnosticsReportError(RuntimeDiagnosticsError):
    """Raised when a diagnostics report is not found."""

    default_code = ErrorCode.NOT_FOUND


class DiagnosticsAlertError(RuntimeDiagnosticsError):
    """Raised when a diagnostics alert operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class DiagnosticsCollectorError(RuntimeDiagnosticsError):
    """Raised when a diagnostics collector operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class DiagnosticsSnapshotError(RuntimeDiagnosticsError):
    """Raised when a diagnostics snapshot is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "DiagnosticsAlertError",
    "DiagnosticsCheckError",
    "DiagnosticsCollectorError",
    "DiagnosticsConfigError",
    "DiagnosticsProbeError",
    "DiagnosticsReportError",
    "DiagnosticsSnapshotError",
    "RuntimeDiagnosticsError",
]
