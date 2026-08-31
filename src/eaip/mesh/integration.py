"""Runtime module integration for the service mesh."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.mesh.circuit_integration import CircuitBreakerIntegration
from eaip.mesh.health import MeshHealthCheck
from eaip.mesh.load_balancer import LoadBalancer
from eaip.mesh.models import MeshConfig
from eaip.mesh.registry import ServiceRegistry
from eaip.mesh.routing import ServiceRouter

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class MeshRuntimeModule:
    name: str = "mesh"

    def __init__(
        self,
        config: MeshConfig | None = None,
        registry: ServiceRegistry | None = None,
        router: ServiceRouter | None = None,
        load_balancer: LoadBalancer | None = None,
        circuit_breaker: CircuitBreakerIntegration | None = None,
        event_bus: Any = None,
    ) -> None:
        self._config = config or MeshConfig()
        self._event_bus = event_bus
        self._registry = registry or ServiceRegistry(event_bus=event_bus)
        self._load_balancer = load_balancer or LoadBalancer(event_bus=event_bus)
        self._router = router or ServiceRouter(
            registry=self._registry,
            load_balancer=self._load_balancer,
            event_bus=event_bus,
        )
        self._circuit_breaker = circuit_breaker or CircuitBreakerIntegration(event_bus=event_bus)
        self._log = get_logger("eaip.mesh.integration")

    @property
    def registry(self) -> ServiceRegistry:
        return self._registry

    @property
    def router(self) -> ServiceRouter:
        return self._router

    @property
    def load_balancer(self) -> LoadBalancer:
        return self._load_balancer

    @property
    def circuit_breaker(self) -> CircuitBreakerIntegration:
        return self._circuit_breaker

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("mesh.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.mesh",
            title="Service Mesh",
            description="Service registry, health-based routing, load balancing, and circuit breaker integration",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("mesh", "routing", "load-balancing", "circuit-breaker", "registry"),
        )
        platform.capabilities.register(capability)
        platform.health.register(MeshHealthCheck(registry=self._registry, router=self._router))
        self._log.info("mesh.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("mesh.module.stopping")


__all__ = ["MeshRuntimeModule"]
