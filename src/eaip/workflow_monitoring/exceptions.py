"""Exception hierarchy for the workflow_monitoring package."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class WorkflowMonitorError(EAIPError):
    """Base exception for all workflow-monitoring errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class WorkflowMonitorConfigError(WorkflowMonitorError):
    """Raised when a monitor configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID

    def __init__(self, message: str) -> None:
        """Initialize WorkflowMonitorConfigError.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message)


class WorkflowMonitorNotFoundError(WorkflowMonitorError):
    """Raised when a requested workflow monitor does not exist."""

    default_code = ErrorCode.NOT_FOUND

    def __init__(self, config_id: str) -> None:
        """Initialize WorkflowMonitorNotFoundError.

        Args:
            config_id: The identifier of the missing monitor config.
        """
        self.config_id = config_id
        super().__init__(f"workflow monitor not found: {config_id!r}")


class WorkflowMonitorAlertError(WorkflowMonitorError):
    """Raised when an alert operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        """Initialize WorkflowMonitorAlertError.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message)


class WorkflowMonitorDashboardError(WorkflowMonitorError):
    """Raised when a dashboard operation fails."""

    default_code = ErrorCode.NOT_FOUND

    def __init__(self, dashboard_id: str) -> None:
        """Initialize WorkflowMonitorDashboardError.

        Args:
            dashboard_id: The identifier of the missing dashboard.
        """
        self.dashboard_id = dashboard_id
        super().__init__(f"dashboard not found: {dashboard_id!r}")


__all__ = [
    "WorkflowMonitorAlertError",
    "WorkflowMonitorConfigError",
    "WorkflowMonitorDashboardError",
    "WorkflowMonitorError",
    "WorkflowMonitorNotFoundError",
]
