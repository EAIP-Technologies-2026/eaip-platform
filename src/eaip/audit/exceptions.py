"""Exception hierarchy for the audit subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class AuditError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class AuditEventNotFoundError(AuditError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class PolicyNotFoundError(AuditError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ClassificationError(AuditError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


class LegalHoldError(AuditError):
    default_code = ErrorCode.POLICY_VIOLATION
    default_severity = ErrorSeverity.ERROR


class ComplianceError(AuditError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "AuditError",
    "AuditEventNotFoundError",
    "ClassificationError",
    "ComplianceError",
    "LegalHoldError",
    "PolicyNotFoundError",
]
