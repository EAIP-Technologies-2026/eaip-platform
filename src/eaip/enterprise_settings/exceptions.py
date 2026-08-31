"""Exception hierarchy for the enterprise settings module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class EnterpriseSettingsError(EAIPError):
    """Base error for the enterprise settings module."""

    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class EnterpriseSettingsNotFoundError(EnterpriseSettingsError):
    """Raised when a requested setting is not found."""

    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class EnterpriseSettingsValidationError(EnterpriseSettingsError):
    """Raised when a setting fails validation."""

    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


class EnterpriseSettingsCategoryError(EnterpriseSettingsError):
    """Raised when a category operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


class EnterpriseSettingsProfileError(EnterpriseSettingsError):
    """Raised when a profile operation fails."""

    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class EnterpriseSettingsExportError(EnterpriseSettingsError):
    """Raised when settings export fails."""

    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class EnterpriseSettingsImportError(EnterpriseSettingsError):
    """Raised when settings import fails."""

    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class EnterpriseSettingsPermissionError(EnterpriseSettingsError):
    """Raised when a settings permission check fails."""

    default_code = ErrorCode.POLICY_VIOLATION
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "EnterpriseSettingsCategoryError",
    "EnterpriseSettingsError",
    "EnterpriseSettingsExportError",
    "EnterpriseSettingsImportError",
    "EnterpriseSettingsNotFoundError",
    "EnterpriseSettingsPermissionError",
    "EnterpriseSettingsProfileError",
    "EnterpriseSettingsValidationError",
]
