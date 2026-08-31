"""Domain events for the metering and usage service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class UsageRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.metering.usage.recorded"

    record_id: str
    tenant_id: str
    metric_name: str
    metric_value: float


class UsageThresholdReached(DomainEvent):
    event_type: ClassVar[str] = "eaip.metering.usage.threshold_reached"

    tenant_id: str
    metric_name: str
    current_value: float
    threshold: float


class AggregateComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.metering.aggregate.computed"

    metric_name: str
    tenant_id: str
    period: str
    total_value: float


__all__ = [
    "AggregateComputed",
    "UsageRecorded",
    "UsageThresholdReached",
]
