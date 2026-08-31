"""Domain events for platform health."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class SnapshotTaken(DomainEvent):
    """Emitted when a health snapshot is taken."""

    event_type: ClassVar[str] = "eaip.phealth.snapshot.taken"

    snapshot_id: str
    component: str
    status: str


class MetricThresholdBreached(DomainEvent):
    """Emitted when a health metric threshold is breached."""

    event_type: ClassVar[str] = "eaip.phealth.metric.threshold_breached"

    metric_name: str
    value: float
    threshold: float
    severity: str = Field(default="warning")


class AlertTriggered(DomainEvent):
    """Emitted when a health alert is triggered."""

    event_type: ClassVar[str] = "eaip.phealth.alert.triggered"

    alert_id: str
    metric_name: str
    component: str
    severity: str


class AlertResolved(DomainEvent):
    """Emitted when a health alert is resolved."""

    event_type: ClassVar[str] = "eaip.phealth.alert.resolved"

    alert_id: str
    metric_name: str
    component: str


__all__ = [
    "AlertResolved",
    "AlertTriggered",
    "MetricThresholdBreached",
    "SnapshotTaken",
]
