"""Exception hierarchy for the schema registry subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class SchemaError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class SchemaNotFoundError(SchemaError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class SchemaVersionNotFoundError(SchemaError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class SchemaValidationError(SchemaError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


class CompatibilityError(SchemaError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "CompatibilityError",
    "SchemaError",
    "SchemaNotFoundError",
    "SchemaValidationError",
    "SchemaVersionNotFoundError",
]
