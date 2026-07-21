"""Security-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class SecurityError(EAIPError):
    """Base exception for all security module errors."""

    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class SecretNotFoundError(SecurityError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND


class EncryptionError(SecurityError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class DecryptionError(SecurityError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class CertificateNotFoundError(SecurityError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND


class CertificateExpiredError(SecurityError):
    default_code: ErrorCode = ErrorCode.POLICY_VIOLATION
    default_severity: ErrorSeverity = ErrorSeverity.WARNING


class ComplianceCheckError(SecurityError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR
