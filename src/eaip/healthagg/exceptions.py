"""Exception hierarchy for the Health Aggregator."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class HealthAggError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ComponentNotFoundError(HealthAggError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class DependencyNotFoundError(HealthAggError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class StatusPageNotFoundError(HealthAggError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class SnapshotNotFoundError(HealthAggError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "ComponentNotFoundError",
    "DependencyNotFoundError",
    "HealthAggError",
    "SnapshotNotFoundError",
    "StatusPageNotFoundError",
]
