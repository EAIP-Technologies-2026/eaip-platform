"""Exception hierarchy for disaster recovery."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class DrError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class PlanNotFoundError(DrError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class StepExecutionError(DrError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class FailoverError(DrError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


class DrTestError(DrError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class RtoViolationError(DrError):
    default_code = ErrorCode.POLICY_VIOLATION
    default_severity = ErrorSeverity.CRITICAL


__all__ = [
    "DrError",
    "DrTestError",
    "FailoverError",
    "PlanNotFoundError",
    "RtoViolationError",
    "StepExecutionError",
]
