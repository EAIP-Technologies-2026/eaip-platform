"""Exception hierarchy for the performance management framework."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class PerfError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_severity: ErrorSeverity = ErrorSeverity.ERROR


class BenchmarkNotFoundError(PerfError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND
    default_severity: ErrorSeverity = ErrorSeverity.WARNING


class BenchmarkRunError(PerfError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_severity: ErrorSeverity = ErrorSeverity.ERROR


class LoadTestError(PerfError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_severity: ErrorSeverity = ErrorSeverity.ERROR


class RegressionNotFoundError(PerfError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND
    default_severity: ErrorSeverity = ErrorSeverity.WARNING


class PerfConfigError(PerfError):
    default_code: ErrorCode = ErrorCode.CONFIGURATION_INVALID
    default_severity: ErrorSeverity = ErrorSeverity.WARNING
