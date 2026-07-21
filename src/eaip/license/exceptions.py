"""Exception hierarchy for license & entitlement management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class LicenseError(EAIPError):
    """Base exception for license-related errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class LicenseNotFoundError(LicenseError):
    """Raised when a requested license does not exist."""

    default_code = ErrorCode.NOT_FOUND


class LicenseExpiredError(LicenseError):
    """Raised when an operation is attempted on an expired license."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


class LicenseRevokedError(LicenseError):
    """Raised when an operation is attempted on a revoked license."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN


class FeatureNotEntitledError(LicenseError):
    """Raised when a feature is not entitled by the license."""

    default_code = ErrorCode.POLICY_VIOLATION


class QuotaExceededError(LicenseError):
    """Raised when a license quota is exceeded."""

    default_code = ErrorCode.POLICY_VIOLATION


class ValidationError(LicenseError):
    """Raised when license validation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "FeatureNotEntitledError",
    "LicenseError",
    "LicenseExpiredError",
    "LicenseNotFoundError",
    "LicenseRevokedError",
    "QuotaExceededError",
    "ValidationError",
]
