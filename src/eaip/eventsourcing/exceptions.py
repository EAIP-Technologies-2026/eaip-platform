"""Exception hierarchy for the event sourcing subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class EventSourcingError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class EventStoreError(EventSourcingError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ProjectionNotFoundError(EventSourcingError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ReplayError(EventSourcingError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class SnapshotNotFoundError(EventSourcingError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ConcurrencyError(EventSourcingError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "ConcurrencyError",
    "EventSourcingError",
    "EventStoreError",
    "ProjectionNotFoundError",
    "ReplayError",
    "SnapshotNotFoundError",
]
