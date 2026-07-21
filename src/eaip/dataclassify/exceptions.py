"""Exception hierarchy for the data classification module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ClassificationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ClassNotFoundError(ClassificationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "ClassNotFoundError",
    "ClassificationError",
]
