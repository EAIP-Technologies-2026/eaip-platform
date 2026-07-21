"""Data quality exception classes."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DataQualityError(EAIPError):
    """Base exception for data quality errors."""

    default_code = ErrorCode.UNKNOWN


class QualityRuleNotFoundError(DataQualityError):
    """Raised when a quality rule is not found."""

    default_code = ErrorCode.NOT_FOUND


class QualityCheckNotFoundError(DataQualityError):
    """Raised when a quality check is not found."""

    default_code = ErrorCode.NOT_FOUND


class QualityCheckError(DataQualityError):
    """Raised when a quality check execution fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class ValidationError(DataQualityError):
    """Raised when data fails validation."""

    default_code = ErrorCode.VALIDATION_FAILED


__all__ = [
    "DataQualityError",
    "QualityCheckError",
    "QualityCheckNotFoundError",
    "QualityRuleNotFoundError",
    "ValidationError",
]
