"""Provider routing service — route management, strategy-based selection, load balancing, and failover."""  # noqa: E501

from __future__ import annotations

import secrets
from collections import defaultdict
from typing import Any

from eaip.logging.context import get_logger
from eaip.provider_routing.events import (
    ProviderEndpointHealthUpdated,
    ProviderFailoverExecuted,
    ProviderRouteActivated,
    ProviderRouteAuditLogged,
    ProviderRouteCreated,
    ProviderRouteDeactivated,
    ProviderRouteDeleted,
    ProviderRouteMetricsCollected,
    ProviderRouteSelected,
    ProviderRouteUpdated,
)
from eaip.provider_routing.exceptions import (
    ProviderEndpointUnavailableError,
    ProviderFallbackError,
    ProviderRouteConfigError,
    ProviderRouteEvaluationError,
    ProviderRouteNotFoundError,
)
from eaip.provider_routing.models import (
    EndpointHealth,
    FailoverConfig,
    ProviderEndpoint,
    ProviderRoute,
    ProviderRouteAssignment,
    ProviderRouteConfig,
    RouteMetrics,
    RouteStatus,
    RoutingStrategy,
)
from eaip.shared.time import utc_now


class ProviderRoutingService:
    """Manages provider routes with strategy-based selection, load balancing, and failover."""

    def __init__(
        self,
        event_bus: Any = None,
        logger: Any | None = None,
    ) -> None:
        """Initialize the routing service with optional event bus and logger."""
        self._routes: dict[str, ProviderRoute] = {}
        self._metrics: dict[str, RouteMetrics] = {}
        self._health: dict[str, EndpointHealth] = {}
        self._endpoint_routes: dict[str, list[str]] = defaultdict(list)
        self._round_robin_index: dict[str, int] = defaultdict(int)
        self._circuit_open: dict[str, float] = {}
        self._event_bus = event_bus
        self._log = logger or get_logger("eaip.provider_routing.service")

    # ------------------------------------------------------------------
    # Route management
    # ------------------------------------------------------------------

    async def create_route(
        self,
        route_id: str,
        config: ProviderRouteConfig,
        name: str = "",
        tags: tuple[str, ...] = (),
    ) -> ProviderRoute:
        """Create a new provider route with the given configuration."""
        if route_id in self._routes:
            raise ProviderRouteConfigError(
                f"Route '{route_id}' already exists",
                context={"route_id": route_id},
            )
        now = utc_now()
        route = ProviderRoute(
            route_id=route_id,
            name=name,
            config=config,
            created_at=now,
            updated_at=now,
            tags=tags,
        )
        self._routes[route_id] = route
        self._metrics[route_id] = RouteMetrics(route_id=route_id)
        for ep in config.load_balancer.endpoints:
            self._endpoint_routes[ep.endpoint_id].append(route_id)
            self._health[ep.endpoint_id] = EndpointHealth(
                endpoint_id=ep.endpoint_id,
                healthy=True,
                last_checked=now,
            )
        await self._publish(ProviderRouteCreated(route_id=route_id, config=config.model_dump()))
        return route

    async def update_route(
        self,
        route_id: str,
        config: ProviderRouteConfig | None = None,
        name: str | None = None,
        tags: tuple[str, ...] | None = None,
    ) -> ProviderRoute:
        """Update an existing provider route's configuration or metadata."""
        route = self._get_route(route_id)
        now = utc_now()
        changes: dict[str, Any] = {}
        if config is not None:
            old_ep_ids = {ep.endpoint_id for ep in route.config.load_balancer.endpoints}
            new_ep_ids = {ep.endpoint_id for ep in config.load_balancer.endpoints}
            for removed in old_ep_ids - new_ep_ids:
                self._endpoint_routes[removed].remove(route_id)
            for added in new_ep_ids - old_ep_ids:
                self._endpoint_routes[added].append(route_id)
                self._health[added] = EndpointHealth(
                    endpoint_id=added,
                    healthy=True,
                    last_checked=now,
                )
            route = ProviderRoute(
                route_id=route_id,
                name=name or route.name,
                status=route.status,
                config=config,
                created_at=route.created_at,
                updated_at=now,
                tags=tags or route.tags,
            )
            changes["config"] = config.model_dump()
        else:
            route = ProviderRoute(
                route_id=route_id,
                name=name or route.name,
                status=route.status,
                config=route.config,
                created_at=route.created_at,
                updated_at=now,
                tags=tags or route.tags,
            )
        if name is not None:
            changes["name"] = name
        if tags is not None:
            changes["tags"] = list(tags)
        self._routes[route_id] = route
        await self._publish(ProviderRouteUpdated(route_id=route_id, changes=changes))
        return route

    async def delete_route(self, route_id: str) -> None:
        """Delete a provider route by its identifier."""
        route = self._get_route(route_id)
        for ep in route.config.load_balancer.endpoints:
            if route_id in self._endpoint_routes[ep.endpoint_id]:
                self._endpoint_routes[ep.endpoint_id].remove(route_id)
        self._routes.pop(route_id, None)
        self._metrics.pop(route_id, None)
        self._round_robin_index.pop(route_id, None)
        await self._publish(ProviderRouteDeleted(route_id=route_id))

    async def activate_route(self, route_id: str) -> ProviderRoute:
        """Activate a provider route."""
        route = self._get_route(route_id)
        if route.status is RouteStatus.ACTIVE:
            return route
        updated = ProviderRoute(
            route_id=route_id,
            name=route.name,
            status=RouteStatus.ACTIVE,
            config=route.config,
            created_at=route.created_at,
            updated_at=utc_now(),
            tags=route.tags,
        )
        self._routes[route_id] = updated
        await self._publish(ProviderRouteActivated(route_id=route_id))
        return updated

    async def deactivate_route(self, route_id: str) -> ProviderRoute:
        """Deactivate a provider route."""
        route = self._get_route(route_id)
        if route.status is RouteStatus.INACTIVE:
            return route
        updated = ProviderRoute(
            route_id=route_id,
            name=route.name,
            status=RouteStatus.INACTIVE,
            config=route.config,
            created_at=route.created_at,
            updated_at=utc_now(),
            tags=route.tags,
        )
        self._routes[route_id] = updated
        await self._publish(ProviderRouteDeactivated(route_id=route_id))
        return updated

    def get_route(self, route_id: str) -> ProviderRoute:
        """Retrieve a provider route by its identifier."""
        return self._get_route(route_id)

    def list_routes(self) -> tuple[ProviderRoute, ...]:
        """Return all provider routes."""
        return tuple(self._routes.values())

    # ------------------------------------------------------------------
    # Strategy-based selection
    # ------------------------------------------------------------------

    async def select_route(
        self,
        request_id: str,
        criteria: dict[str, Any] | None = None,
        _correlation_id: object | None = None,
    ) -> ProviderRouteAssignment:
        """Select a route for the given request based on criteria."""
        available = self._available_routes()
        if not available:
            raise ProviderRouteNotFoundError(
                "No active routes available",
                context={"request_id": request_id},
            )

        route = self._evaluate_rules(available, criteria or {})

        endpoint = await self._select_endpoint(route)
        assignment = ProviderRouteAssignment(
            request_id=request_id,
            route_id=route.route_id,
            endpoint_id=endpoint.endpoint_id,
            strategy=route.config.strategy,
        )
        await self._publish(
            ProviderRouteSelected(
                route_id=route.route_id,
                request_id=request_id,
                assignment=assignment,
            ),
        )
        return assignment

    async def select_route_for_request(
        self,
        request_id: str,
        route_id: str,
        _correlation_id: object | None = None,
    ) -> ProviderRouteAssignment:
        """Select a specific route for a request by route identifier."""
        route = self._get_route(route_id)
        if route.status is not RouteStatus.ACTIVE:
            raise ProviderRouteEvaluationError(
                f"Route '{route_id}' is not active",
                context={"route_id": route_id, "status": route.status.value},
            )

        endpoint = await self._select_endpoint(route)
        assignment = ProviderRouteAssignment(
            request_id=request_id,
            route_id=route.route_id,
            endpoint_id=endpoint.endpoint_id,
            strategy=route.config.strategy,
        )
        await self._publish(
            ProviderRouteSelected(
                route_id=route.route_id,
                request_id=request_id,
                assignment=assignment,
            ),
        )
        return assignment

    def evaluate_routes(
        self,
        criteria: dict[str, Any],
    ) -> tuple[ProviderRoute, ...]:
        """Evaluate all active routes against the given criteria."""
        available = self._available_routes()
        return tuple(route for route in available if self._match_criteria(route, criteria))

    # ------------------------------------------------------------------
    # Load balancing
    # ------------------------------------------------------------------

    async def _select_endpoint(self, route: ProviderRoute) -> ProviderEndpoint:
        strategy = route.config.strategy
        endpoints = list(route.config.load_balancer.endpoints)

        healthy = [ep for ep in endpoints if self._is_endpoint_available(ep)]
        if not healthy:
            return await self._execute_failover(route, endpoints)

        return self._apply_strategy(strategy, route.route_id, healthy)

    def _apply_strategy(
        self,
        strategy: RoutingStrategy,
        route_id: str,
        endpoints: list[ProviderEndpoint],
    ) -> ProviderEndpoint:
        strategy_map = {
            RoutingStrategy.ROUND_ROBIN: self._round_robin,
            RoutingStrategy.WEIGHTED: self._weighted,
            RoutingStrategy.LEAST_LOADED: self._least_loaded,
            RoutingStrategy.PRIORITY: self._priority,
            RoutingStrategy.HEALTH_FIRST: self._health_first,
            RoutingStrategy.RANDOM: self._random,
            RoutingStrategy.SEMANTIC: self._semantic,
        }
        handler = strategy_map.get(strategy, self._round_robin)

        return handler(route_id, endpoints)

    def _round_robin(self, route_id: str, endpoints: list[ProviderEndpoint]) -> ProviderEndpoint:
        idx = self._round_robin_index[route_id] % len(endpoints)
        self._round_robin_index[route_id] = idx + 1
        return endpoints[idx]

    def _random(self, _route_id: str, endpoints: list[ProviderEndpoint]) -> ProviderEndpoint:
        return endpoints[secrets.randbelow(len(endpoints))]

    def _weighted(self, _route_id: str, endpoints: list[ProviderEndpoint]) -> ProviderEndpoint:
        total = sum(max(ep.weight, 1) for ep in endpoints)
        threshold = secrets.randbelow(total)
        cumulative = 0
        for ep in endpoints:
            cumulative += max(ep.weight, 1)
            if threshold < cumulative:
                return ep
        return endpoints[-1]

    def _least_loaded(self, _route_id: str, endpoints: list[ProviderEndpoint]) -> ProviderEndpoint:
        return min(
            endpoints,
            key=lambda ep: (
                self._metrics.get(
                    ep.endpoint_id,
                    RouteMetrics(route_id=ep.endpoint_id),
                ).total_requests
            ),
        )

    def _priority(self, _route_id: str, endpoints: list[ProviderEndpoint]) -> ProviderEndpoint:
        return min(endpoints, key=lambda ep: ep.priority)

    def _health_first(self, _route_id: str, endpoints: list[ProviderEndpoint]) -> ProviderEndpoint:
        healthy = [
            ep
            for ep in endpoints
            if self._health.get(
                ep.endpoint_id,
                EndpointHealth(endpoint_id=ep.endpoint_id, healthy=True),
            ).healthy
        ]
        return healthy[0] if healthy else endpoints[0]

    def _semantic(self, _route_id: str, endpoints: list[ProviderEndpoint]) -> ProviderEndpoint:
        return min(
            endpoints,
            key=lambda ep: (
                self._health.get(
                    ep.endpoint_id, EndpointHealth(endpoint_id=ep.endpoint_id, healthy=True)
                ).latency_ms,
                ep.priority,
            ),
        )


    # ------------------------------------------------------------------
    # Failover
    # ------------------------------------------------------------------

    async def _execute_failover(
        self,
        route: ProviderRoute,
        endpoints: list[ProviderEndpoint],
    ) -> ProviderEndpoint:
        failover = route.config.failover
        if not failover.enabled:
            raise ProviderEndpointUnavailableError(
                "No healthy endpoints and failover is disabled",
                context={"route_id": route.route_id},
            )

        for attempt in range(failover.max_attempts):
            first_id = endpoints[0].endpoint_id if endpoints else ""
            available = [ep for ep in endpoints if ep.endpoint_id != first_id]
            if not available and failover.fallback_endpoint_id:
                fallback = next(
                    (ep for ep in endpoints if ep.endpoint_id == failover.fallback_endpoint_id),
                    None,
                )
                if fallback:
                    return fallback
            healthy_alt = [ep for ep in available if self._is_endpoint_available(ep)]
            if healthy_alt:
                await self._publish(
                    ProviderFailoverExecuted(
                        route_id=route.route_id,
                        request_id="",
                        from_endpoint_id=endpoints[0].endpoint_id if endpoints else "",
                        to_endpoint_id=healthy_alt[0].endpoint_id,
                        attempt=attempt + 1,
                    ),
                )
                return healthy_alt[0]

        raise ProviderFallbackError(
            "All failover attempts exhausted",
            context={"route_id": route.route_id, "max_attempts": failover.max_attempts},
        )

    async def failover(
        self,
        route_id: str,
        request_id: str,
        from_endpoint_id: str,
    ) -> ProviderRouteAssignment:
        """Execute failover for a route, switching to a healthy endpoint."""
        route = self._get_route(route_id)
        endpoints = list(route.config.load_balancer.endpoints)

        for attempt in range(route.config.failover.max_attempts):
            alternatives = [ep for ep in endpoints if ep.endpoint_id != from_endpoint_id]
            healthy_alt = [ep for ep in alternatives if self._is_endpoint_available(ep)]
            if healthy_alt:
                target = healthy_alt[0]
                await self._publish(
                    ProviderFailoverExecuted(
                        route_id=route_id,
                        request_id=request_id,
                        from_endpoint_id=from_endpoint_id,
                        to_endpoint_id=target.endpoint_id,
                        attempt=attempt + 1,
                    ),
                )
                return ProviderRouteAssignment(
                    request_id=request_id,
                    route_id=route_id,
                    endpoint_id=target.endpoint_id,
                    strategy=route.config.strategy,
                )

        raise ProviderFallbackError(
            "Failover failed for route",
            context={"route_id": route_id, "max_attempts": route.config.failover.max_attempts},
        )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def report_health(
        self,
        endpoint_id: str,
        healthy: bool,
        latency_ms: float = 0.0,
        details: dict[str, Any] | None = None,
    ) -> EndpointHealth:
        """Report health status for a given endpoint."""
        now = utc_now()
        current = self._health.get(
            endpoint_id,
            EndpointHealth(endpoint_id=endpoint_id, healthy=True),
        )
        error_count = (current.error_count + 1) if not healthy else 0
        health = EndpointHealth(
            endpoint_id=endpoint_id,
            healthy=healthy,
            last_checked=now,
            latency_ms=latency_ms,
            error_count=error_count,
            details=details or {},
        )
        self._health[endpoint_id] = health

        if not healthy:
            failover_config = self._find_failover_config(endpoint_id)
            if failover_config and error_count >= failover_config.circuit_breaker_threshold:
                self._circuit_open[endpoint_id] = now.timestamp()

        await self._publish(ProviderEndpointHealthUpdated(endpoint_id=endpoint_id, health=health))
        return health

    def get_endpoint_health(self, endpoint_id: str) -> EndpointHealth | None:
        """Get the current health snapshot for an endpoint."""
        return self._health.get(endpoint_id)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    async def record_request(
        self,
        route_id: str,
        success: bool,
        latency_ms: float,
    ) -> RouteMetrics:
        """Record a request result for a route and update metrics."""
        current = self._metrics.get(
            route_id,
            RouteMetrics(route_id=route_id),
        )
        total = current.total_requests + 1
        successful = current.successful_requests + (1 if success else 0)
        failed = current.failed_requests + (0 if success else 1)
        total_latency = current.total_latency_ms + latency_ms
        average_latency = total_latency / total if total else 0.0
        metrics = RouteMetrics(
            route_id=route_id,
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            total_latency_ms=total_latency,
            average_latency_ms=average_latency,
            last_request_at=utc_now(),
        )
        self._metrics[route_id] = metrics
        await self._publish(ProviderRouteMetricsCollected(route_id=route_id, metrics=metrics))
        return metrics

    def get_metrics(self, route_id: str) -> RouteMetrics | None:
        """Get metrics for a specific route."""
        return self._metrics.get(route_id)

    def get_all_metrics(self) -> dict[str, RouteMetrics]:
        """Get metrics for all routes."""
        return dict(self._metrics)

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    async def audit_log(
        self,
        route_id: str,
        action: str,
        actor: str = "system",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record an audit entry for a route action."""
        await self._publish(
            ProviderRouteAuditLogged(
                route_id=route_id,
                action=action,
                actor=actor,
                details=details or {},
            ),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_route(self, route_id: str) -> ProviderRoute:
        route = self._routes.get(route_id)
        if route is None:
            raise ProviderRouteNotFoundError(
                f"Route '{route_id}' not found",
                context={"route_id": route_id},
            )
        return route

    def _available_routes(self) -> list[ProviderRoute]:
        return [r for r in self._routes.values() if r.status is RouteStatus.ACTIVE]

    def _evaluate_rules(
        self,
        available: list[ProviderRoute],
        criteria: dict[str, Any],
    ) -> ProviderRoute:
        sorted_routes = sorted(
            available,
            key=lambda r: min(
                (rule.priority for rule in r.config.rules),
                default=0,
            ),
        )
        for route in sorted_routes:
            if self._match_criteria(route, criteria):
                return route
        return sorted_routes[0] if sorted_routes else available[0]

    def _match_criteria(self, route: ProviderRoute, criteria: dict[str, Any]) -> bool:
        model = criteria.get("model")
        if model and route.route_id != model:
            return False
        provider_id = criteria.get("provider_id")
        return not (
            provider_id
            and not any(
                ep.provider_id == provider_id for ep in route.config.load_balancer.endpoints
            )
        )

    def _is_endpoint_available(self, endpoint: ProviderEndpoint) -> bool:
        health = self._health.get(endpoint.endpoint_id)
        if health is None:
            return True
        if not health.healthy:
            return False
        open_at = self._circuit_open.get(endpoint.endpoint_id)
        if open_at is not None:
            config = self._find_failover_config(endpoint.endpoint_id)
            reset_seconds = config.circuit_breaker_reset_seconds if config else 60.0
            if utc_now().timestamp() - open_at < reset_seconds:
                return False
            self._circuit_open.pop(endpoint.endpoint_id, None)
        return True

    def _find_failover_config(self, endpoint_id: str) -> FailoverConfig | None:
        for route_id in self._endpoint_routes.get(endpoint_id, []):
            route = self._routes.get(route_id)
            if route:
                return route.config.failover
        return None

    async def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                await self._event_bus.publish(event)
            except Exception:
                self._log.warning("Failed to publish event", event_type=type(event).__name__)

    async def health_check(self) -> dict[str, Any]:
        """Return aggregate health status of the routing subsystem."""
        return {
            "total_routes": len(self._routes),
            "active_routes": len(self._available_routes()),
            "total_endpoints": len(self._health),
            "healthy_endpoints": sum(1 for h in self._health.values() if h.healthy),
            "circuit_open_count": len(self._circuit_open),
        }


__all__ = ["ProviderRoutingService"]
