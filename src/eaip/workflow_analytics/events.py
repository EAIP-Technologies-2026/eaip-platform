"""Workflow analytics domain events — published via EventBus during analytics operations."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class WorkflowMetricsCollected(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow_analytics.metrics.collected"
    workflow_id: str = ""
    total_executions: int = 0
    succeeded: int = 0
    failed: int = 0


class WorkflowAnalyticsReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow_analytics.report.generated"
    report_id: str = ""
    workflow_id: str = ""
    period: str = ""


class BottleneckDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow_analytics.bottleneck.detected"
    workflow_id: str = ""
    bottleneck_type: str = ""
    severity: str = "medium"
    affected_steps: tuple[str, ...] = ()
    avg_wait_time_seconds: float = 0.0


class PerformanceTrendComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow_analytics.performance.trend.computed"
    workflow_id: str = ""
    metric_name: str = ""
    direction: str = "stable"
    change_percent: float = 0.0
    confidence: float = 0.0


class WorkflowThroughputAnalyzed(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow_analytics.throughput.analyzed"
    workflow_id: str = ""
    total_executions: int = 0
    executions_per_hour: float = 0.0
    peak_hour: str = ""


class WorkflowSlaComplianceComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow_analytics.sla.compliance.computed"
    workflow_id: str = ""
    compliance_pct: float = 0.0
    sla_threshold_seconds: float = 0.0
    total_executions: int = 0


class WorkflowAnalyticsConfigUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.workflow_analytics.config.updated"
    changes: dict[str, Any] = {}
    previous_config: dict[str, Any] = {}


WorkflowAnalyticsEvent = (
    WorkflowMetricsCollected
    | WorkflowAnalyticsReportGenerated
    | BottleneckDetected
    | PerformanceTrendComputed
    | WorkflowThroughputAnalyzed
    | WorkflowSlaComplianceComputed
    | WorkflowAnalyticsConfigUpdated
)


__all__ = [
    "BottleneckDetected",
    "PerformanceTrendComputed",
    "WorkflowAnalyticsConfigUpdated",
    "WorkflowAnalyticsEvent",
    "WorkflowAnalyticsReportGenerated",
    "WorkflowMetricsCollected",
    "WorkflowSlaComplianceComputed",
    "WorkflowThroughputAnalyzed",
]
