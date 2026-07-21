from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class AiObservabilityError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AiTraceError(AiObservabilityError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AiSpanError(AiObservabilityError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AiObservabilityConfigError(AiObservabilityError):
    default_code = ErrorCode.CONFIGURATION_INVALID
    default_severity = ErrorSeverity.WARNING


class AiObservabilityReportError(AiObservabilityError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AiObservabilityAlertError(AiObservabilityError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "AiObservabilityAlertError",
    "AiObservabilityConfigError",
    "AiObservabilityError",
    "AiObservabilityReportError",
    "AiSpanError",
    "AiTraceError",
]
