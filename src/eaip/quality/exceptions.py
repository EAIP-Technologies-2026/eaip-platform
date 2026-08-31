"""Exception hierarchy for the quality & testing framework."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class QualityError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_severity: ErrorSeverity = ErrorSeverity.ERROR


class TestCaseNotFoundError(QualityError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND
    default_severity: ErrorSeverity = ErrorSeverity.WARNING


class TestExecutionError(QualityError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    default_severity: ErrorSeverity = ErrorSeverity.ERROR


class SuiteNotFoundError(QualityError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND
    default_severity: ErrorSeverity = ErrorSeverity.WARNING


class QualityGateError(QualityError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND
    default_severity: ErrorSeverity = ErrorSeverity.WARNING


class CoverageError(QualityError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND
    default_severity: ErrorSeverity = ErrorSeverity.WARNING


class RegressionDetectionError(QualityError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND
    default_severity: ErrorSeverity = ErrorSeverity.WARNING
