"""Domain events for the service mesh."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.mesh.models import RoutingStrategy, ServiceStatus


class ServiceRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.service.registered"

    service_id: str = Field(description="Registered service instance ID.")
    service_name: str = Field(description="Service name.")


class ServiceUnregistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.service.unregistered"

    service_id: str = Field(description="Unregistered service instance ID.")
    service_name: str = Field(description="Service name.")


class ServiceHealthChanged(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.service.health_changed"

    service_id: str = Field(description="Service instance ID.")
    service_name: str = Field(description="Service name.")
    old_status: ServiceStatus = Field(description="Previous health status.")
    new_status: ServiceStatus = Field(description="New health status.")


class RouteCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.route.created"

    route_id: str = Field(description="Route ID.")
    name: str = Field(description="Route name.")
    source_service: str = Field(description="Source service name.")
    destination_service: str = Field(description="Destination service name.")
    strategy: RoutingStrategy = Field(description="Routing strategy.")


class RouteUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.route.updated"

    route_id: str = Field(description="Route ID.")
    name: str = Field(description="Route name.")
    source_service: str = Field(description="Source service name.")
    destination_service: str = Field(description="Destination service name.")
    strategy: RoutingStrategy = Field(description="Routing strategy.")


class CircuitBreakerTripped(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.circuit_breaker.tripped"

    service_name: str = Field(description="Service name whose circuit opened.")
    failure_count: int = Field(description="Failure count at trip time.")


class CircuitBreakerReset(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.circuit_breaker.reset"

    service_name: str = Field(description="Service name whose circuit reset.")


class LoadBalanced(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.load_balancer.balanced"

    service_name: str = Field(description="Service name.")
    strategy: RoutingStrategy = Field(description="Strategy used.")
    selected_instance_id: str = Field(description="Selected instance ID.")


class ModelRerouted(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.model.rerouted"
    model_id: str
    provider: str
    endpoint: str


class ModelRouteFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.mesh.model.route.failed"
    model_id: str
    reason: str


__all__ = [
    "CircuitBreakerReset",
    "CircuitBreakerTripped",
    "LoadBalanced",
    "ModelRerouted",
    "ModelRouteFailed",
    "RouteCreated",
    "RouteUpdated",
    "ServiceHealthChanged",
    "ServiceRegistered",
    "ServiceUnregistered",
]
