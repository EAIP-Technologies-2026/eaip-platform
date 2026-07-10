"""Analytics domain events — published via EventBus during analytics operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class MetricRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.analytics.metric.recorded"
    metric_id: str = ""
    value: float = 0.0
    tags: dict[str, str] = {}
    source: str = ""


class ReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.analytics.report.generated"
    report_id: str = ""
    name: str = ""
    metric_ids: tuple[str, ...] = ()
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None


class KpiEvaluated(DomainEvent):
    event_type: ClassVar[str] = "eaip.analytics.kpi.evaluated"
    kpi_id: str = ""
    current_value: float = 0.0
    target_value: float = 0.0
    status: str = ""
    progress: float = 0.0


class AnomalyDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.analytics.anomaly.detected"
    metric_id: str = ""
    value: float = 0.0
    expected_value: float = 0.0
    deviation: float = 0.0
    severity: str = ""


class DashboardCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.analytics.dashboard.created"
    dashboard_id: str = ""
    name: str = ""
    widget_count: int = 0


class DashboardUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.analytics.dashboard.updated"
    dashboard_id: str = ""
    changes: dict[str, Any] = {}
    previous_version: int = 0


class TrendComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.analytics.trend.computed"
    metric_id: str = ""
    direction: str = ""
    change_percent: float = 0.0
    confidence: float = 0.0
    period_comparison: dict[str, float] = {}
    anomaly_count: int = 0


AnalyticsEvent = (
    MetricRecorded
    | ReportGenerated
    | KpiEvaluated
    | AnomalyDetected
    | DashboardCreated
    | DashboardUpdated
    | TrendComputed
)


__all__ = [
    "AnalyticsEvent",
    "AnomalyDetected",
    "DashboardCreated",
    "DashboardUpdated",
    "KpiEvaluated",
    "MetricRecorded",
    "ReportGenerated",
    "TrendComputed",
]
