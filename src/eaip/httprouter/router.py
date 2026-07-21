"""HTTP request router service — route registration, matching, lifecycle management."""

from __future__ import annotations

from eaip.httprouter.exceptions import RouteNotFoundError
from eaip.httprouter.models import Route, RouteMatch, RouterConfig, RouteStatus


class HTTPRequestRouter:
    def __init__(self, config: RouterConfig | None = None) -> None:
        self._config = config or RouterConfig()
        self._routes: dict[str, Route] = {}
        self._matches: dict[str, RouteMatch] = {}

    @property
    def config(self) -> RouterConfig:
        return self._config

    async def register_route(self, route: Route) -> Route:
        self._routes[route.id] = route
        return route

    async def get_route(self, route_id: str) -> Route:
        route = self._routes.get(route_id)
        if route is None:
            raise RouteNotFoundError(f"Route {route_id} not found")
        return route

    async def deactivate_route(self, route_id: str) -> Route:
        route = await self.get_route(route_id)
        updated = route.model_copy(update={"status": RouteStatus.INACTIVE})
        self._routes[route_id] = updated
        return updated

    async def record_match(self, match: RouteMatch) -> RouteMatch:
        self._matches[f"{match.route_id}:{match.request_path}"] = match
        return match

    async def list_routes(self) -> list[Route]:
        return list(self._routes.values())

    async def list_active_routes(self) -> list[Route]:
        return [r for r in self._routes.values() if r.status is RouteStatus.ACTIVE]


__all__ = ["HTTPRequestRouter"]
