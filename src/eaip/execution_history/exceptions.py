"""Exception hierarchy for the execution history subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ExecutionHistoryError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ExecutionRecordNotFoundError(ExecutionHistoryError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ExecutionHistoryQueryError(ExecutionHistoryError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ExecutionHistoryArchiveError(ExecutionHistoryError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ExecutionHistoryPurgeError(ExecutionHistoryError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ExecutionHistoryExportError(ExecutionHistoryError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "ExecutionHistoryArchiveError",
    "ExecutionHistoryError",
    "ExecutionHistoryExportError",
    "ExecutionHistoryPurgeError",
    "ExecutionHistoryQueryError",
    "ExecutionRecordNotFoundError",
]
