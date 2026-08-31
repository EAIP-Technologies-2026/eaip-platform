"""Domain events for runtime diagnostics."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.runtime_diagnostics.models import (
    DiagnosticsCollectorStatus,
    DiagnosticsMetricType,
    DiagnosticsReportSeverity,
    RuntimeDiagnosticsConfig,
)


class RuntimeDiagnosticsConfigUpdated(DomainEvent):
    """Emitted when the runtime diagnostics configuration is updated."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.config.updated"

    old_config: RuntimeDiagnosticsConfig | None = None
    new_config: RuntimeDiagnosticsConfig


class DiagnosticsProbeCreated(DomainEvent):
    """Emitted when a diagnostics probe is created."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.probe.created"

    probe_id: str
    name: str
    probe_type: str
    target: str


class DiagnosticsProbeExecuted(DomainEvent):
    """Emitted when a diagnostics probe is executed."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.probe.executed"

    probe_id: str
    status: str
    latency_ms: float
    message: str = ""


class DiagnosticsProbeFailed(DomainEvent):
    """Emitted when a diagnostics probe execution fails."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.probe.failed"

    probe_id: str
    error_message: str
    details: dict[str, Any] | None = None


class DiagnosticsCheckStarted(DomainEvent):
    """Emitted when a diagnostics check is started."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.check.started"

    check_id: str
    name: str


class DiagnosticsCheckCompleted(DomainEvent):
    """Emitted when a diagnostics check completes."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.check.completed"

    check_id: str
    name: str
    status: str
    result_count: int = 0


class DiagnosticsCheckFailed(DomainEvent):
    """Emitted when a diagnostics check fails."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.check.failed"

    check_id: str
    name: str
    error_message: str
    details: dict[str, Any] | None = None


class DiagnosticsReportGenerated(DomainEvent):
    """Emitted when a diagnostics report is generated."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.report.generated"

    report_id: str
    title: str
    severity: DiagnosticsReportSeverity
    check_count: int = 0


class DiagnosticsAlertTriggered(DomainEvent):
    """Emitted when a diagnostics alert is triggered."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.alert.triggered"

    alert_id: str
    rule_name: str
    message: str
    severity: DiagnosticsReportSeverity
    details: dict[str, Any] | None = None


class DiagnosticsAlertResolved(DomainEvent):
    """Emitted when a diagnostics alert is resolved."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.alert.resolved"

    alert_id: str
    rule_name: str
    resolved_at: datetime


class DiagnosticsSnapshotTaken(DomainEvent):
    """Emitted when a diagnostics snapshot is taken."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.snapshot.taken"

    snapshot_id: str
    label: str
    snapshot_type: str
    size_bytes: int = 0


class DiagnosticsMetricCollected(DomainEvent):
    """Emitted when a diagnostics metric is collected."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.metric.collected"

    name: str
    type: DiagnosticsMetricType
    value: float
    labels: dict[str, str] | None = None
    unit: str = ""


class DiagnosticsHistoryEntryRecorded(DomainEvent):
    """Emitted when a history entry is recorded."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.history.recorded"

    entry_id: str
    action: str
    component: str
    severity: DiagnosticsReportSeverity
    message: str = ""


class DiagnosticsDashboardUpdated(DomainEvent):
    """Emitted when a diagnostics dashboard is updated."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.dashboard.updated"

    dashboard_id: str
    dashboard_name: str


class DiagnosticsCollectorStatusChanged(DomainEvent):
    """Emitted when a diagnostics collector status changes."""

    event_type: ClassVar[str] = "eaip.runtime_diagnostics.collector.status_changed"

    collector_id: str
    name: str
    old_status: DiagnosticsCollectorStatus | None = None
    new_status: DiagnosticsCollectorStatus


__all__ = [
    "DiagnosticsAlertResolved",
    "DiagnosticsAlertTriggered",
    "DiagnosticsCheckCompleted",
    "DiagnosticsCheckFailed",
    "DiagnosticsCheckStarted",
    "DiagnosticsCollectorStatusChanged",
    "DiagnosticsDashboardUpdated",
    "DiagnosticsHistoryEntryRecorded",
    "DiagnosticsMetricCollected",
    "DiagnosticsProbeCreated",
    "DiagnosticsProbeExecuted",
    "DiagnosticsProbeFailed",
    "DiagnosticsReportGenerated",
    "DiagnosticsSnapshotTaken",
    "RuntimeDiagnosticsConfigUpdated",
]
