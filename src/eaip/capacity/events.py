"""Domain events for capacity analysis."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class MetricRecorded(DomainEvent):
    """Emitted when a resource metric is recorded."""

    event_type: ClassVar[str] = "eaip.capacity.metric.recorded"

    metric_id: str
    resource_id: str
    metric_name: str
    value: float


class CapacityReportGenerated(DomainEvent):
    """Emitted when a capacity report is generated."""

    event_type: ClassVar[str] = "eaip.capacity.report.generated"

    report_id: str
    resource_id: str
    current_usage: float
    predicted_usage: float
    recommended_capacity: float


class ThresholdBreached(DomainEvent):
    """Emitted when a usage threshold is breached."""

    event_type: ClassVar[str] = "eaip.capacity.threshold.breached"

    resource_id: str
    metric_name: str
    current_value: float
    threshold: float
    threshold_type: str


__all__ = [
    "CapacityReportGenerated",
    "MetricRecorded",
    "ThresholdBreached",
]
