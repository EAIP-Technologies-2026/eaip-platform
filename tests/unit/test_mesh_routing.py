"""Tests for :mod:`eaip.mesh.routing`."""

from __future__ import annotations

import pytest

from eaip.mesh.exceptions import RouteNotFoundError
from eaip.mesh.models import RoutingStrategy, ServiceInstance, ServiceRoute, ServiceStatus
from eaip.mesh.registry import ServiceRegistry
from eaip.mesh.routing import ServiceRouter


@pytest.fixture
def registry() -> ServiceRegistry:
    return ServiceRegistry()


@pytest.fixture
def router(registry: ServiceRegistry) -> ServiceRouter:
    return ServiceRouter(registry=registry)


@pytest.fixture
def healthy_instances(registry: ServiceRegistry) -> list[ServiceInstance]:
    instances = [
        ServiceInstance(id="s1", name="users", host="10.0.0.1", port=8080, status=ServiceStatus.UP),
        ServiceInstance(id="s2", name="users", host="10.0.0.2", port=8080, status=ServiceStatus.UP),
    ]
    for inst in instances:
        registry.register(inst)
    return instances


class TestServiceRouter:
    def test_register_route(self, router: ServiceRouter) -> None:
        route = ServiceRoute(
            id="r-1",
            name="auth-to-users",
            source_service="auth",
            destination_service="users",
        )
        result = router.register_route(route)
        assert result.id == "r-1"
        assert router.get_route("r-1") == route

    def test_unregister_route(self, router: ServiceRouter) -> None:
        route = ServiceRoute(
            id="r-1",
            name="t",
            source_service="a",
            destination_service="b",
        )
        router.register_route(route)
        router.unregister_route("r-1")
        with pytest.raises(RouteNotFoundError):
            router.get_route("r-1")

    def test_unregister_not_found(self, router: ServiceRouter) -> None:
        with pytest.raises(RouteNotFoundError):
            router.unregister_route("nonexistent")

    def test_get_route_not_found(self, router: ServiceRouter) -> None:
        with pytest.raises(RouteNotFoundError):
            router.get_route("nonexistent")

    def test_list_routes(self, router: ServiceRouter) -> None:
        route = ServiceRoute(
            id="r-1",
            name="t",
            source_service="a",
            destination_service="b",
        )
        router.register_route(route)
        routes = router.list_routes()
        assert len(routes) == 1
        assert routes[0].id == "r-1"

    @pytest.mark.asyncio
    async def test_route_request_with_route(
        self,
        router: ServiceRouter,
        healthy_instances: list[ServiceInstance],
    ) -> None:
        route = ServiceRoute(
            id="r-1",
            name="auth-to-users",
            source_service="auth",
            destination_service="users",
            routing_strategy=RoutingStrategy.ROUND_ROBIN,
        )
        router.register_route(route)
        instance = await router.route_request(source="auth", destination="users")
        assert instance.name == "users"
        assert instance.status is ServiceStatus.UP

    @pytest.mark.asyncio
    async def test_route_request_no_route_falls_back_to_healthy(
        self,
        router: ServiceRouter,
        healthy_instances: list[ServiceInstance],
    ) -> None:
        instance = await router.route_request(source="gateway", destination="users")
        assert instance.name == "users"

    @pytest.mark.asyncio
    async def test_route_request_disabled_route_with_fallback(
        self,
        router: ServiceRouter,
        registry: ServiceRegistry,
    ) -> None:
        registry.register(
            ServiceInstance(
                id="fb", name="users-backup", host="h", port=80, status=ServiceStatus.UP
            )
        )
        route = ServiceRoute(
            id="r-1",
            name="t",
            source_service="a",
            destination_service="users",
            enabled=False,
            fallback_service="users-backup",
        )
        router.register_route(route)
        instance = await router.route_request(source="a", destination="users")
        assert instance.name == "users-backup"

    def test_update_route(self, router: ServiceRouter) -> None:
        route = ServiceRoute(
            id="r-1",
            name="original",
            source_service="a",
            destination_service="b",
        )
        router.register_route(route)
        updated = router.update_route("r-1", name="updated")
        assert updated.name == "updated"
        assert router.get_route("r-1").name == "updated"

    def test_update_route_not_found(self, router: ServiceRouter) -> None:
        with pytest.raises(RouteNotFoundError):
            router.update_route("nonexistent", name="x")
