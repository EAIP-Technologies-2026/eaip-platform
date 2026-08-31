"""Domain events for the Health Aggregator."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.health.checks import HealthStatus


class HealthCheckCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.check_completed"
    component: str
    status: HealthStatus
    duration_ms: float


class ComponentStatusChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.component_status_changed"
    component: str
    previous_status: HealthStatus
    new_status: HealthStatus


class DependencyImpactDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.dependency_impact_detected"
    source_component: str
    affected_components: tuple[str, ...]


class StatusPageCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.status_page_created"
    page_id: str
    page_name: str


class StatusPageUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.status_page_updated"
    page_id: str
    page_name: str


class SnapshotCaptured(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.snapshot_captured"
    snapshot_id: str
    overall_status: HealthStatus
    component_count: int


class HealthDegraded(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.health_degraded"
    component: str
    previous_status: HealthStatus
    current_status: HealthStatus


class HealthRestored(DomainEvent):
    event_type: ClassVar[str] = "eaip.healthagg.health_restored"
    component: str
    previous_status: HealthStatus
    current_status: HealthStatus


__all__ = [
    "ComponentStatusChanged",
    "DependencyImpactDetected",
    "HealthCheckCompleted",
    "HealthDegraded",
    "HealthRestored",
    "SnapshotCaptured",
    "StatusPageCreated",
    "StatusPageUpdated",
]
