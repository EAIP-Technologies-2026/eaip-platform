"""Exception hierarchy for the compensation runtime."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class CompensationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class CompensationPlanNotFoundError(CompensationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class CompensationExecutionError(CompensationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class CompensationStepError(CompensationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class CompensationRollbackError(CompensationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class CompensationConfigError(CompensationError):
    default_code = ErrorCode.CONFIGURATION_INVALID
    default_severity = ErrorSeverity.WARNING


class CompensationPlanValidationError(CompensationError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "CompensationConfigError",
    "CompensationError",
    "CompensationExecutionError",
    "CompensationPlanNotFoundError",
    "CompensationPlanValidationError",
    "CompensationRollbackError",
    "CompensationStepError",
]
