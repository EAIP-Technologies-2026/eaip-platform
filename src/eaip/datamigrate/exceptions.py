"""Exception hierarchy for the data migration module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class MigrationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class MigrationNotFoundError(MigrationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class MigrationFailedError(MigrationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class RollbackFailedError(MigrationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class TransformError(MigrationError):
    default_code = ErrorCode.TRANSFORM_ERROR
    default_severity = ErrorSeverity.ERROR


class ValidationError(MigrationError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "MigrationError",
    "MigrationFailedError",
    "MigrationNotFoundError",
    "RollbackFailedError",
    "TransformError",
    "ValidationError",
]
