"""Exception hierarchy for the configuration management module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ConfigMgtError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ConfigNotFoundError(ConfigMgtError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ConfigValidationError(ConfigMgtError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


class ProfileNotFoundError(ConfigMgtError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class SnapshotNotFoundError(ConfigMgtError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ConfigTypeError(ConfigMgtError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "ConfigMgtError",
    "ConfigNotFoundError",
    "ConfigTypeError",
    "ConfigValidationError",
    "ProfileNotFoundError",
    "SnapshotNotFoundError",
]
