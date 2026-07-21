"""Domain events for the enterprise health reporter."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ReportGenerated(DomainEvent):
    """Emitted when a health report is generated."""

    event_type: ClassVar[str] = "eaip.healthrpt.report.generated"

    report_id: str
    overall_status: str
    sla_achievement: float


class SLAViolation(DomainEvent):
    """Emitted when a component violates its SLA target."""

    event_type: ClassVar[str] = "eaip.healthrpt.sla.violation"

    component_id: str
    component_name: str
    sla_target: float
    actual_achievement: float


class ComponentStatusChanged(DomainEvent):
    """Emitted when a component's health status changes."""

    event_type: ClassVar[str] = "eaip.healthrpt.component.status_changed"

    component_id: str
    component_name: str
    previous_status: str
    new_status: str


__all__ = [
    "ComponentStatusChanged",
    "ReportGenerated",
    "SLAViolation",
]
