from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.ai_observability.models import (
    AiModelCallMetrics,
    AiObservabilityAlertSeverity,
    AiObservabilityConfig,
    AiTraceSpanStatus,
    MetricType,
    SpanKind,
)
from eaip.events.event import DomainEvent


class AiTraceStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.trace.started"
    trace_id: str
    name: str
    attributes: dict[str, Any] | None = None


class AiTraceSpanStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.trace.span.started"
    span_id: str
    trace_id: str
    parent_span_id: str | None = None
    name: str
    kind: SpanKind = SpanKind.INTERNAL
    attributes: dict[str, Any] | None = None


class AiTraceSpanCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.trace.span.completed"
    span_id: str
    trace_id: str
    status: AiTraceSpanStatus = AiTraceSpanStatus.OK
    end_time: datetime | None = None
    attributes: dict[str, Any] | None = None


class AiTraceSpanFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.trace.span.failed"
    span_id: str
    trace_id: str
    error_message: str
    error_type: str = ""
    attributes: dict[str, Any] | None = None


class AiModelCallLogged(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.model_call.logged"
    call_id: str
    model_name: str
    provider: str
    deployment_name: str = ""
    metrics: AiModelCallMetrics | None = None
    metadata: dict[str, Any] | None = None


class AiObservabilityMetricRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.metric.recorded"
    name: str
    type: MetricType
    value: float
    labels: dict[str, str] | None = None
    unit: str = ""


class AiObservabilityReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.report.generated"
    report_id: str
    title: str
    period_start: datetime
    period_end: datetime
    trace_count: int = 0
    model_call_count: int = 0
    alert_count: int = 0


class AiObservabilityAlertTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.alert.triggered"
    alert_id: str
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    severity: AiObservabilityAlertSeverity = AiObservabilityAlertSeverity.WARNING
    message: str = ""


class AiObservabilityAlertResolved(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.alert.resolved"
    alert_id: str
    rule_name: str
    resolved_at: datetime | None = None


class AiTraceContextPropagated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.trace.context.propagated"
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    baggage: dict[str, str] | None = None


class AiObservabilityConfigUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.config.updated"
    old_config: AiObservabilityConfig | None = None
    new_config: AiObservabilityConfig


class AiObservabilityDashboardCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.dashboard.created"
    dashboard_id: str
    dashboard_name: str


class AiObservabilityDashboardUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_observability.dashboard.updated"
    dashboard_id: str
    dashboard_name: str


__all__ = [
    "AiModelCallLogged",
    "AiObservabilityAlertResolved",
    "AiObservabilityAlertTriggered",
    "AiObservabilityConfigUpdated",
    "AiObservabilityDashboardCreated",
    "AiObservabilityDashboardUpdated",
    "AiObservabilityMetricRecorded",
    "AiObservabilityReportGenerated",
    "AiTraceContextPropagated",
    "AiTraceSpanCompleted",
    "AiTraceSpanFailed",
    "AiTraceSpanStarted",
    "AiTraceStarted",
]
