"""Service router that selects instances based on routing strategies and routes."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.mesh.events import RouteCreated, RouteUpdated
from eaip.mesh.exceptions import NoHealthyInstanceError, RouteNotFoundError
from eaip.mesh.load_balancer import LoadBalancer
from eaip.mesh.models import RoutingStrategy, ServiceInstance, ServiceRoute
from eaip.mesh.registry import ServiceRegistry


class ServiceRouter:
    """Manages routes and selects service instances based on routing rules."""

    def __init__(
        self,
        registry: ServiceRegistry,
        load_balancer: LoadBalancer | None = None,
        event_bus: Any = None,
    ) -> None:
        self._registry = registry
        self._load_balancer = load_balancer or LoadBalancer(event_bus=event_bus)
        self._routes: dict[str, ServiceRoute] = {}
        self._log = get_logger("eaip.mesh.routing")
        self._event_bus = event_bus

    def register_route(self, route: ServiceRoute) -> ServiceRoute:
        self._routes[route.id] = route
        self._log.info("route.registered", id=route.id, name=route.name)
        if self._event_bus is not None:
            self._event_bus.publish(
                RouteCreated(
                    route_id=route.id,
                    name=route.name,
                    source_service=route.source_service,
                    destination_service=route.destination_service,
                    strategy=route.routing_strategy,
                )
            )
        return route

    def unregister_route(self, route_id: str) -> None:
        route = self._routes.pop(route_id, None)
        if route is None:
            raise RouteNotFoundError(f"Route {route_id!r} not found.")

    def get_route(self, route_id: str) -> ServiceRoute:
        route = self._routes.get(route_id)
        if route is None:
            raise RouteNotFoundError(f"Route {route_id!r} not found.")
        return route

    def list_routes(self) -> list[ServiceRoute]:
        return list(self._routes.values())

    async def route_request(
        self,
        source: str,
        destination: str,
        context: dict[str, Any] | None = None,
    ) -> ServiceInstance:
        matching_routes = [
            r
            for r in self._routes.values()
            if r.source_service == source and r.destination_service == destination
        ]

        route: ServiceRoute | None = None
        if matching_routes:
            route = matching_routes[0]

        if route is None:
            healthy = self._registry.get_healthy_instances(destination)
            return self._load_balancer.get_next_instance(
                destination,
                healthy,
                RoutingStrategy.ROUND_ROBIN,
            )

        if not route.enabled:
            if route.fallback_service:
                return await self.route_request(source, route.fallback_service, context)
            raise NoHealthyInstanceError(
                f"Route {route.id!r} is disabled and no fallback configured.",
            )

        healthy = self._registry.get_healthy_instances(destination)
        return self._load_balancer.get_next_instance(
            destination,
            healthy,
            route.routing_strategy,
        )

    def update_route(self, route_id: str, **updates: Any) -> ServiceRoute:
        existing = self.get_route(route_id)
        updated = existing.model_copy(update=updates)
        self._routes[route_id] = updated
        self._log.info("route.updated", id=route_id)
        if self._event_bus is not None:
            self._event_bus.publish(
                RouteUpdated(
                    route_id=updated.id,
                    name=updated.name,
                    source_service=updated.source_service,
                    destination_service=updated.destination_service,
                    strategy=updated.routing_strategy,
                )
            )
        return updated


__all__ = ["ServiceRouter"]
