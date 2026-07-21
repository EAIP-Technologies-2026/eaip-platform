"""Domain events emitted by the provider routing subsystem."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.provider_routing.models import (
    EndpointHealth,
    ProviderRouteAssignment,
    RouteMetrics,
)


class ProviderRouteCreated(DomainEvent):
    """Published when a provider route is created."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.created"

    route_id: str
    config: dict[str, Any]


class ProviderRouteUpdated(DomainEvent):
    """Published when a provider route is updated."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.updated"

    route_id: str
    changes: dict[str, Any]


class ProviderRouteDeleted(DomainEvent):
    """Published when a provider route is deleted."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.deleted"

    route_id: str


class ProviderRouteActivated(DomainEvent):
    """Published when a provider route is activated."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.activated"

    route_id: str


class ProviderRouteDeactivated(DomainEvent):
    """Published when a provider route is deactivated."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.deactivated"

    route_id: str


class ProviderRouteEvaluated(DomainEvent):
    """Published when a provider route is evaluated for a request."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.evaluated"

    route_id: str
    request_id: str
    matched: bool


class ProviderRouteSelected(DomainEvent):
    """Published when a provider route is selected for a request."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.selected"

    route_id: str
    request_id: str
    assignment: ProviderRouteAssignment


class ProviderRouteFailed(DomainEvent):
    """Published when a provider route fails to handle a request."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.failed"

    route_id: str
    request_id: str
    error: str
    attempt: int


class ProviderRouteFallbackTriggered(DomainEvent):
    """Published when a fallback route is triggered."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.fallback_triggered"

    route_id: str
    request_id: str
    fallback_endpoint_id: str
    reason: str


class ProviderEndpointHealthUpdated(DomainEvent):
    """Published when endpoint health status changes."""

    event_type: ClassVar[str] = "eaip.provider_routing.endpoint.health_updated"

    endpoint_id: str
    health: EndpointHealth


class ProviderRouteMetricsCollected(DomainEvent):
    """Published when route metrics are collected."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.metrics_collected"

    route_id: str
    metrics: RouteMetrics


class ProviderLoadBalancerConfigUpdated(DomainEvent):
    """Published when a load balancer configuration is updated."""

    event_type: ClassVar[str] = "eaip.provider_routing.load_balancer.config_updated"

    route_id: str
    config: dict[str, Any]


class ProviderFailoverExecuted(DomainEvent):
    """Published when a failover is executed."""

    event_type: ClassVar[str] = "eaip.provider_routing.failover.executed"

    route_id: str
    request_id: str
    from_endpoint_id: str
    to_endpoint_id: str
    attempt: int


class ProviderRouteAuditLogged(DomainEvent):
    """Published when a route audit entry is logged."""

    event_type: ClassVar[str] = "eaip.provider_routing.route.audit_logged"

    route_id: str
    action: str
    actor: str
    details: dict[str, Any]


__all__ = [
    "ProviderEndpointHealthUpdated",
    "ProviderFailoverExecuted",
    "ProviderLoadBalancerConfigUpdated",
    "ProviderRouteActivated",
    "ProviderRouteAuditLogged",
    "ProviderRouteCreated",
    "ProviderRouteDeactivated",
    "ProviderRouteDeleted",
    "ProviderRouteEvaluated",
    "ProviderRouteFailed",
    "ProviderRouteFallbackTriggered",
    "ProviderRouteMetricsCollected",
    "ProviderRouteSelected",
    "ProviderRouteUpdated",
]
