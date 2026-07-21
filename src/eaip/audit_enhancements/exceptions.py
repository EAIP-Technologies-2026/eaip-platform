"""Exception hierarchy for the audit enhancements subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class AuditEnhancementError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditCorrelationError(AuditEnhancementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditEnrichmentError(AuditEnhancementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditAggregationError(AuditEnhancementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditAlertError(AuditEnhancementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditStreamError(AuditEnhancementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditReportError(AuditEnhancementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditEnhancementConfigError(AuditEnhancementError):
    default_code = ErrorCode.CONFIGURATION_INVALID
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "AuditAggregationError",
    "AuditAlertError",
    "AuditCorrelationError",
    "AuditEnhancementConfigError",
    "AuditEnhancementError",
    "AuditEnrichmentError",
    "AuditReportError",
    "AuditStreamError",
]
