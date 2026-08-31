"""Exception hierarchy for the data masking module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class DataMaskError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class MaskingRuleNotFoundError(DataMaskError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class AnonymizationError(DataMaskError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class PiiDetectionError(DataMaskError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "AnonymizationError",
    "DataMaskError",
    "MaskingRuleNotFoundError",
    "PiiDetectionError",
]
