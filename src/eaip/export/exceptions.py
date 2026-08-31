"""Exception hierarchy for the export & reporting engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ExportError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ReportNotFoundError(ExportError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ExportFailedError(ExportError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class FormatNotSupportedError(ExportError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


class DeliveryFailedError(ExportError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


class ScheduleNotFoundError(ExportError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "DeliveryFailedError",
    "ExportError",
    "ExportFailedError",
    "FormatNotSupportedError",
    "ReportNotFoundError",
    "ScheduleNotFoundError",
]
