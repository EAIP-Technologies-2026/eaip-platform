"""Exception hierarchy for the data sampling module."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class SamplingError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class DefinitionNotFoundError(SamplingError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "DefinitionNotFoundError",
    "SamplingError",
]
