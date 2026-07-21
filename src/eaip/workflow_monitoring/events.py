"""Domain events raised by the workflow_monitoring package."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class WorkflowMonitorCreated(DomainEvent):
    """Published when a workflow monitor configuration is created."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.created"
    config_id: str = ""
    workflow_name: str = ""


class WorkflowMonitorUpdated(DomainEvent):
    """Published when a workflow monitor configuration is updated."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.updated"
    config_id: str = ""
    changes: dict[str, Any] = Field(default_factory=dict)


class WorkflowMonitorDeleted(DomainEvent):
    """Published when a workflow monitor configuration is deleted."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.deleted"
    config_id: str = ""
    workflow_name: str = ""


class WorkflowMonitorActivated(DomainEvent):
    """Published when a workflow monitor is activated."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.activated"
    config_id: str = ""
    workflow_name: str = ""


class WorkflowMonitorDeactivated(DomainEvent):
    """Published when a workflow monitor is deactivated."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.deactivated"
    config_id: str = ""
    workflow_name: str = ""


class WorkflowMonitorAlertTriggered(DomainEvent):
    """Published when a monitor threshold is breached and an alert fires."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.alert.triggered"
    alert_id: str = ""
    config_id: str = ""
    severity: str = ""
    metric_name: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    message: str = ""


class WorkflowMonitorAlertResolved(DomainEvent):
    """Published when a previously triggered alert is resolved."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.alert.resolved"
    alert_id: str = ""
    config_id: str = ""
    resolved_at: datetime | None = None


class WorkflowMonitorSnapshotTaken(DomainEvent):
    """Published when a point-in-time monitor snapshot is captured."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.snapshot.taken"
    snapshot_id: str = ""
    config_id: str = ""
    status: str = ""
    healthy: bool = True


class WorkflowMonitorThresholdBreached(DomainEvent):
    """Published when a threshold rule is breached by a metric value."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.threshold.breached"
    threshold_id: str = ""
    config_id: str = ""
    metric_name: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    severity: str = ""


class WorkflowMonitorStatusChanged(DomainEvent):
    """Published when a monitor's status transitions to a new value."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.status.changed"
    config_id: str = ""
    previous_status: str = ""
    current_status: str = ""


class WorkflowMonitorReportGenerated(DomainEvent):
    """Published when a monitoring report is generated."""

    event_type: ClassVar[str] = "eaip.workflow_monitoring.report.generated"
    report_id: str = ""
    config_ids: tuple[str, ...] = ()
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None


WorkflowMonitorEvent = (
    WorkflowMonitorCreated
    | WorkflowMonitorUpdated
    | WorkflowMonitorDeleted
    | WorkflowMonitorActivated
    | WorkflowMonitorDeactivated
    | WorkflowMonitorAlertTriggered
    | WorkflowMonitorAlertResolved
    | WorkflowMonitorSnapshotTaken
    | WorkflowMonitorThresholdBreached
    | WorkflowMonitorStatusChanged
    | WorkflowMonitorReportGenerated
)


__all__ = [
    "WorkflowMonitorActivated",
    "WorkflowMonitorAlertResolved",
    "WorkflowMonitorAlertTriggered",
    "WorkflowMonitorCreated",
    "WorkflowMonitorDeactivated",
    "WorkflowMonitorDeleted",
    "WorkflowMonitorEvent",
    "WorkflowMonitorReportGenerated",
    "WorkflowMonitorSnapshotTaken",
    "WorkflowMonitorStatusChanged",
    "WorkflowMonitorThresholdBreached",
    "WorkflowMonitorUpdated",
]
