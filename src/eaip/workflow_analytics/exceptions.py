"""Workflow analytics exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class WorkflowAnalyticsError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class WorkflowAnalyticsConfigError(WorkflowAnalyticsError):
    default_code: ErrorCode = ErrorCode.CONFIGURATION_INVALID

    def __init__(self, message: str) -> None:
        super().__init__(message)


class WorkflowAnalyticsReportError(WorkflowAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class WorkflowAnalyticsQueryError(WorkflowAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class WorkflowAnalyticsDataNotFoundError(WorkflowAnalyticsError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"workflow analytics data not found: {workflow_id!r}")


__all__ = [
    "WorkflowAnalyticsConfigError",
    "WorkflowAnalyticsDataNotFoundError",
    "WorkflowAnalyticsError",
    "WorkflowAnalyticsQueryError",
    "WorkflowAnalyticsReportError",
]
