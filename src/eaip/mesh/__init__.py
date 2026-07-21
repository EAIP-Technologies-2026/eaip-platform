"""Service mesh — service registry, health-based routing, load balancing, and circuit breaker integration."""

from __future__ import annotations

from eaip.mesh.circuit_integration import CircuitBreakerIntegration
from eaip.mesh.events import (
    CircuitBreakerReset,
    CircuitBreakerTripped,
    LoadBalanced,
    RouteCreated,
    RouteUpdated,
    ServiceHealthChanged,
    ServiceRegistered,
    ServiceUnregistered,
)
from eaip.mesh.exceptions import (
    CircuitBreakerOpenError,
    LoadBalancerError,
    MeshError,
    NoHealthyInstanceError,
    RouteNotFoundError,
    ServiceNotFoundError,
)
from eaip.mesh.health import MeshHealthCheck
from eaip.mesh.integration import MeshRuntimeModule
from eaip.mesh.load_balancer import LoadBalancer
from eaip.mesh.models import (
    LoadBalancerState,
    MeshConfig,
    ServiceInstance,
    ServiceRoute,
)
from eaip.mesh.registry import ServiceRegistry
from eaip.mesh.routing import ServiceRouter

__all__ = [
    "CircuitBreakerIntegration",
    "CircuitBreakerOpenError",
    "CircuitBreakerReset",
    "CircuitBreakerTripped",
    "LoadBalanced",
    "LoadBalancer",
    "LoadBalancerError",
    "LoadBalancerState",
    "MeshConfig",
    "MeshError",
    "MeshHealthCheck",
    "MeshRuntimeModule",
    "NoHealthyInstanceError",
    "RouteCreated",
    "RouteNotFoundError",
    "RouteUpdated",
    "ServiceHealthChanged",
    "ServiceInstance",
    "ServiceRegistered",
    "ServiceRegistry",
    "ServiceRoute",
    "ServiceRouter",
    "ServiceUnregistered",
]
