"""Provider Routing — intelligent route management.

Supports multiple routing strategies (round-robin, weighted, least-loaded,
priority, health-first, random) with configurable health checking, circuit
breakers, and failover for resilient provider endpoint management.
"""

from __future__ import annotations

from eaip.provider_routing.events import (
    ProviderEndpointHealthUpdated,
    ProviderFailoverExecuted,
    ProviderLoadBalancerConfigUpdated,
    ProviderRouteActivated,
    ProviderRouteAuditLogged,
    ProviderRouteCreated,
    ProviderRouteDeactivated,
    ProviderRouteDeleted,
    ProviderRouteEvaluated,
    ProviderRouteFailed,
    ProviderRouteFallbackTriggered,
    ProviderRouteMetricsCollected,
    ProviderRouteSelected,
    ProviderRouteUpdated,
)
from eaip.provider_routing.exceptions import (
    ProviderEndpointUnavailableError,
    ProviderFallbackError,
    ProviderLoadBalancerError,
    ProviderRouteConfigError,
    ProviderRouteEvaluationError,
    ProviderRouteMetricsError,
    ProviderRouteNotFoundError,
    ProviderRoutingError,
)
from eaip.provider_routing.health import ProviderRoutingHealthCheck
from eaip.provider_routing.integration import ProviderRoutingRuntimeModule
from eaip.provider_routing.models import (
    EndpointHealth,
    FailoverConfig,
    HealthCheckConfig,
    LoadBalancerConfig,
    ProviderEndpoint,
    ProviderRoute,
    ProviderRouteAssignment,
    ProviderRouteConfig,
    RouteAuditEntry,
    RouteMatchCriteria,
    RouteMetrics,
    RouteStatus,
    RouteWeight,
    RoutingRule,
    RoutingStrategy,
)
from eaip.provider_routing.service import ProviderRoutingService

__all__ = [
    "EndpointHealth",
    "FailoverConfig",
    "HealthCheckConfig",
    "LoadBalancerConfig",
    "ProviderEndpoint",
    "ProviderEndpointHealthUpdated",
    "ProviderEndpointUnavailableError",
    "ProviderFailoverExecuted",
    "ProviderFallbackError",
    "ProviderLoadBalancerConfigUpdated",
    "ProviderLoadBalancerError",
    "ProviderRoute",
    "ProviderRouteActivated",
    "ProviderRouteAssignment",
    "ProviderRouteAuditLogged",
    "ProviderRouteConfig",
    "ProviderRouteConfigError",
    "ProviderRouteCreated",
    "ProviderRouteDeactivated",
    "ProviderRouteDeleted",
    "ProviderRouteEvaluated",
    "ProviderRouteEvaluationError",
    "ProviderRouteFailed",
    "ProviderRouteFallbackTriggered",
    "ProviderRouteMetricsCollected",
    "ProviderRouteMetricsError",
    "ProviderRouteNotFoundError",
    "ProviderRouteSelected",
    "ProviderRouteUpdated",
    "ProviderRoutingError",
    "ProviderRoutingHealthCheck",
    "ProviderRoutingRuntimeModule",
    "ProviderRoutingService",
    "RouteAuditEntry",
    "RouteMatchCriteria",
    "RouteMetrics",
    "RouteStatus",
    "RouteWeight",
    "RoutingRule",
    "RoutingStrategy",
]
