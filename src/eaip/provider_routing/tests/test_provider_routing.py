"""Tests for the provider routing subsystem."""

from __future__ import annotations

import pytest

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
from eaip.provider_routing.models import (
    EndpointHealth,
    FailoverConfig,
    LoadBalancerConfig,
    ProviderEndpoint,
    ProviderRoute,
    ProviderRouteConfig,
    RouteMetrics,
    RouteStatus,
    RoutingStrategy,
)
from eaip.provider_routing.service import ProviderRoutingService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service() -> ProviderRoutingService:
    return ProviderRoutingService()


@pytest.fixture
def endpoint_a() -> ProviderEndpoint:
    return ProviderEndpoint(endpoint_id="ep-a", provider_id="p1", url="http://a.example.com")


@pytest.fixture
def endpoint_b() -> ProviderEndpoint:
    return ProviderEndpoint(endpoint_id="ep-b", provider_id="p1", url="http://b.example.com")


@pytest.fixture
def endpoint_c() -> ProviderEndpoint:
    return ProviderEndpoint(endpoint_id="ep-c", provider_id="p2", url="http://c.example.com")


@pytest.fixture
def route_config() -> ProviderRouteConfig:
    return ProviderRouteConfig()


@pytest.fixture
async def populated_service(
    service: ProviderRoutingService,
    endpoint_a: ProviderEndpoint,
    endpoint_b: ProviderEndpoint,
) -> ProviderRoutingService:
    config = ProviderRouteConfig(
        load_balancer=LoadBalancerConfig(
            strategy=RoutingStrategy.ROUND_ROBIN,
            endpoints=(endpoint_a, endpoint_b),
        ),
    )
    await service.create_route("route-1", config, name="Test Route")
    return service


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestRouteStatus:
    def test_members(self) -> None:
        assert RouteStatus.ACTIVE.value == "active"
        assert RouteStatus.INACTIVE.value == "inactive"
        assert RouteStatus.DEGRADED.value == "degraded"
        assert RouteStatus.FAILED.value == "failed"
        assert RouteStatus.DRAINING.value == "draining"

    def test_str_enum(self) -> None:
        assert str(RouteStatus.ACTIVE) == "active"


class TestRoutingStrategy:
    def test_members(self) -> None:
        assert RoutingStrategy.ROUND_ROBIN.value == "round_robin"
        assert RoutingStrategy.WEIGHTED.value == "weighted"
        assert RoutingStrategy.LEAST_LOADED.value == "least_loaded"
        assert RoutingStrategy.PRIORITY.value == "priority"
        assert RoutingStrategy.HEALTH_FIRST.value == "health_first"
        assert RoutingStrategy.RANDOM.value == "random"
        assert RoutingStrategy.CUSTOM.value == "custom"


class TestModelsFrozen:
    def test_provider_route_frozen(self, endpoint_a: ProviderEndpoint) -> None:
        route = ProviderRoute(
            route_id="r1",
            config=ProviderRouteConfig(
                load_balancer=LoadBalancerConfig(endpoints=(endpoint_a,)),
            ),
        )
        with pytest.raises(TypeError):
            route.name = "changed"

    def test_endpoint_health_frozen(self) -> None:
        h = EndpointHealth(endpoint_id="ep-1", healthy=True)
        with pytest.raises(TypeError):
            h.healthy = False

    def test_route_metrics_defaults(self) -> None:
        m = RouteMetrics(route_id="r1")
        assert m.total_requests == 0
        assert m.successful_requests == 0
        assert m.failed_requests == 0
        assert m.total_latency_ms == 0.0
        assert m.circuit_broken is False


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestEvents:
    def test_provider_route_created_event_type(self) -> None:
        assert ProviderRouteCreated.event_type == "eaip.provider_routing.route.created"

    def test_provider_route_updated_event_type(self) -> None:
        assert ProviderRouteUpdated.event_type == "eaip.provider_routing.route.updated"

    def test_provider_route_deleted_event_type(self) -> None:
        assert ProviderRouteDeleted.event_type == "eaip.provider_routing.route.deleted"

    def test_provider_route_activated_event_type(self) -> None:
        assert ProviderRouteActivated.event_type == "eaip.provider_routing.route.activated"

    def test_provider_route_deactivated_event_type(self) -> None:
        assert ProviderRouteDeactivated.event_type == "eaip.provider_routing.route.deactivated"

    def test_provider_route_evaluated_event_type(self) -> None:
        assert ProviderRouteEvaluated.event_type == "eaip.provider_routing.route.evaluated"

    def test_provider_route_selected_event_type(self) -> None:
        assert ProviderRouteSelected.event_type == "eaip.provider_routing.route.selected"

    def test_provider_route_failed_event_type(self) -> None:
        assert ProviderRouteFailed.event_type == "eaip.provider_routing.route.failed"

    def test_provider_route_fallback_triggered_event_type(self) -> None:
        expected = "eaip.provider_routing.route.fallback_triggered"
        assert ProviderRouteFallbackTriggered.event_type == expected

    def test_provider_endpoint_health_updated_event_type(self) -> None:
        assert (
            ProviderEndpointHealthUpdated.event_type
            == "eaip.provider_routing.endpoint.health_updated"
        )

    def test_provider_route_metrics_collected_event_type(self) -> None:
        assert (
            ProviderRouteMetricsCollected.event_type
            == "eaip.provider_routing.route.metrics_collected"
        )

    def test_provider_load_balancer_config_updated_event_type(self) -> None:
        expected = "eaip.provider_routing.load_balancer.config_updated"
        assert ProviderLoadBalancerConfigUpdated.event_type == expected

    def test_provider_failover_executed_event_type(self) -> None:
        assert ProviderFailoverExecuted.event_type == "eaip.provider_routing.failover.executed"

    def test_provider_route_audit_logged_event_type(self) -> None:
        assert ProviderRouteAuditLogged.event_type == "eaip.provider_routing.route.audit_logged"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_provider_routing_error(self) -> None:
        err = ProviderRoutingError("test error")
        assert str(err) == "test error"

    def test_provider_route_not_found_error(self) -> None:
        err = ProviderRouteNotFoundError("not found")
        assert isinstance(err, ProviderRoutingError)

    def test_provider_route_config_error(self) -> None:
        err = ProviderRouteConfigError("bad config")
        assert isinstance(err, ProviderRoutingError)

    def test_provider_route_evaluation_error(self) -> None:
        err = ProviderRouteEvaluationError("evaluation failed")
        assert isinstance(err, ProviderRoutingError)

    def test_provider_endpoint_unavailable_error(self) -> None:
        err = ProviderEndpointUnavailableError("unavailable")
        assert isinstance(err, ProviderRoutingError)

    def test_provider_fallback_error(self) -> None:
        err = ProviderFallbackError("fallback")
        assert isinstance(err, ProviderRoutingError)

    def test_provider_load_balancer_error(self) -> None:
        err = ProviderLoadBalancerError("lb error")
        assert isinstance(err, ProviderRoutingError)

    def test_provider_route_metrics_error(self) -> None:
        err = ProviderRouteMetricsError("metrics error")
        assert isinstance(err, ProviderRoutingError)


# ---------------------------------------------------------------------------
# Service — Route Management
# ---------------------------------------------------------------------------


class TestCreateRoute:
    async def test_create_route(
        self, service: ProviderRoutingService, endpoint_a: ProviderEndpoint
    ) -> None:
        config = ProviderRouteConfig(
            load_balancer=LoadBalancerConfig(endpoints=(endpoint_a,)),
        )
        route = await service.create_route("r1", config, name="my route")
        assert route.route_id == "r1"
        assert route.name == "my route"
        assert route.status is RouteStatus.ACTIVE

    async def test_create_duplicate_raises(self, service: ProviderRoutingService) -> None:
        config = ProviderRouteConfig()
        await service.create_route("dup", config)
        with pytest.raises(ProviderRouteConfigError):
            await service.create_route("dup", config)

    async def test_create_adds_metrics(self, service: ProviderRoutingService) -> None:
        config = ProviderRouteConfig()
        await service.create_route("r2", config)
        metrics = service.get_metrics("r2")
        assert metrics is not None
        assert metrics.route_id == "r2"


class TestUpdateRoute:
    async def test_update_route_name(self, populated_service: ProviderRoutingService) -> None:
        route = await populated_service.update_route("route-1", name="Updated Name")
        assert route.name == "Updated Name"

    async def test_update_route_not_found(self, service: ProviderRoutingService) -> None:
        with pytest.raises(ProviderRouteNotFoundError):
            await service.update_route("nonexistent", name="x")


class TestDeleteRoute:
    async def test_delete_route(self, populated_service: ProviderRoutingService) -> None:
        await populated_service.delete_route("route-1")
        with pytest.raises(ProviderRouteNotFoundError):
            populated_service.get_route("route-1")

    async def test_delete_nonexistent_raises(self, service: ProviderRoutingService) -> None:
        with pytest.raises(ProviderRouteNotFoundError):
            await service.delete_route("nonexistent")


class TestActivateDeactivate:
    async def test_activate(self, populated_service: ProviderRoutingService) -> None:
        await populated_service.deactivate_route("route-1")
        route = await populated_service.activate_route("route-1")
        assert route.status is RouteStatus.ACTIVE

    async def test_deactivate(self, populated_service: ProviderRoutingService) -> None:
        route = await populated_service.deactivate_route("route-1")
        assert route.status is RouteStatus.INACTIVE

    async def test_activate_already_active(self, populated_service: ProviderRoutingService) -> None:
        route = await populated_service.activate_route("route-1")
        assert route.status is RouteStatus.ACTIVE


class TestGetListRoutes:
    async def test_get_route(self, populated_service: ProviderRoutingService) -> None:
        route = populated_service.get_route("route-1")
        assert route.route_id == "route-1"

    async def test_get_route_not_found(self, service: ProviderRoutingService) -> None:
        with pytest.raises(ProviderRouteNotFoundError):
            service.get_route("nonexistent")

    async def test_list_routes(self, populated_service: ProviderRoutingService) -> None:
        routes = populated_service.list_routes()
        assert len(routes) == 1

    async def test_list_routes_empty(self, service: ProviderRoutingService) -> None:
        assert service.list_routes() == ()


# ---------------------------------------------------------------------------
# Service — Route Selection
# ---------------------------------------------------------------------------


class TestSelectRoute:
    async def test_select_route_returns_assignment(
        self,
        populated_service: ProviderRoutingService,
    ) -> None:
        assignment = await populated_service.select_route("req-1")
        assert assignment.request_id == "req-1"
        assert assignment.route_id == "route-1"
        assert assignment.endpoint_id in ("ep-a", "ep-b")

    async def test_select_route_not_found_when_no_routes(
        self, service: ProviderRoutingService
    ) -> None:
        with pytest.raises(ProviderRouteNotFoundError):
            await service.select_route("req-1")

    async def test_select_route_inactive_fails(
        self, service: ProviderRoutingService, endpoint_a: ProviderEndpoint
    ) -> None:
        config = ProviderRouteConfig(
            load_balancer=LoadBalancerConfig(endpoints=(endpoint_a,)),
        )
        await service.create_route("r-inactive", config)
        await service.deactivate_route("r-inactive")
        with pytest.raises(ProviderRouteNotFoundError):
            await service.select_route("req-1")


class TestSelectRouteForRequest:
    async def test_select_route_for_request(
        self,
        populated_service: ProviderRoutingService,
    ) -> None:
        assignment = await populated_service.select_route_for_request("req-1", "route-1")
        assert assignment.route_id == "route-1"

    async def test_select_route_for_request_inactive(
        self,
        populated_service: ProviderRoutingService,
    ) -> None:
        await populated_service.deactivate_route("route-1")
        with pytest.raises(ProviderRouteEvaluationError):
            await populated_service.select_route_for_request("req-1", "route-1")

    async def test_select_route_for_request_not_found(
        self,
        service: ProviderRoutingService,
    ) -> None:
        with pytest.raises(ProviderRouteNotFoundError):
            await service.select_route_for_request("req-1", "nonexistent")


# ---------------------------------------------------------------------------
# Service — Load Balancing
# ---------------------------------------------------------------------------


class TestRoundRobin:
    async def test_round_robin_cycles(
        self,
        service: ProviderRoutingService,
        endpoint_a: ProviderEndpoint,
        endpoint_b: ProviderEndpoint,
    ) -> None:
        config = ProviderRouteConfig(
            strategy=RoutingStrategy.ROUND_ROBIN,
            load_balancer=LoadBalancerConfig(
                strategy=RoutingStrategy.ROUND_ROBIN,
                endpoints=(endpoint_a, endpoint_b),
            ),
        )
        await service.create_route("rr", config)
        a1 = await service.select_route("req-1")
        a2 = await service.select_route("req-2")
        assert a1.endpoint_id != a2.endpoint_id


class TestWeighted:
    async def test_weighted_selects_higher_weight_more_often(
        self,
        service: ProviderRoutingService,
    ) -> None:
        heavy = ProviderEndpoint(
            endpoint_id="heavy",
            provider_id="p1",
            url="http://heavy.example.com",
            weight=10,
        )
        light = ProviderEndpoint(
            endpoint_id="light",
            provider_id="p1",
            url="http://light.example.com",
            weight=1,
        )
        config = ProviderRouteConfig(
            strategy=RoutingStrategy.WEIGHTED,
            load_balancer=LoadBalancerConfig(
                strategy=RoutingStrategy.WEIGHTED,
                endpoints=(heavy, light),
            ),
        )
        await service.create_route("weighted", config)
        selections = {"heavy": 0, "light": 0}
        for i in range(100):
            a = await service.select_route(f"req-{i}")
            selections[a.endpoint_id] += 1
        assert selections["heavy"] > selections["light"]


class TestPriority:
    async def test_priority_selects_lowest_priority(
        self,
        service: ProviderRoutingService,
    ) -> None:
        high = ProviderEndpoint(
            endpoint_id="high",
            provider_id="p1",
            url="http://high.example.com",
            priority=10,
        )
        low = ProviderEndpoint(
            endpoint_id="low",
            provider_id="p1",
            url="http://low.example.com",
            priority=1,
        )
        config = ProviderRouteConfig(
            strategy=RoutingStrategy.PRIORITY,
            load_balancer=LoadBalancerConfig(
                strategy=RoutingStrategy.PRIORITY,
                endpoints=(high, low),
            ),
        )
        await service.create_route("pri", config)
        a = await service.select_route("req-1")
        assert a.endpoint_id == "low"


class TestHealthFirst:
    async def test_health_first_skips_unhealthy(
        self,
        service: ProviderRoutingService,
        endpoint_a: ProviderEndpoint,
        endpoint_b: ProviderEndpoint,
    ) -> None:
        config = ProviderRouteConfig(
            strategy=RoutingStrategy.HEALTH_FIRST,
            load_balancer=LoadBalancerConfig(
                strategy=RoutingStrategy.HEALTH_FIRST,
                endpoints=(endpoint_a, endpoint_b),
            ),
        )
        await service.create_route("hf", config)
        await service.report_health("ep-a", healthy=False)
        a = await service.select_route("req-1")
        assert a.endpoint_id == "ep-b"


class TestRandom:
    async def test_random_selects(
        self,
        service: ProviderRoutingService,
        endpoint_a: ProviderEndpoint,
        endpoint_b: ProviderEndpoint,
    ) -> None:
        config = ProviderRouteConfig(
            strategy=RoutingStrategy.RANDOM,
            load_balancer=LoadBalancerConfig(
                strategy=RoutingStrategy.RANDOM,
                endpoints=(endpoint_a, endpoint_b),
            ),
        )
        await service.create_route("rand", config)
        a = await service.select_route("req-1")
        assert a.endpoint_id in ("ep-a", "ep-b")


# ---------------------------------------------------------------------------
# Service — Health
# ---------------------------------------------------------------------------


class TestHealth:
    async def test_report_healthy(self, service: ProviderRoutingService) -> None:
        health = await service.report_health("ep-1", healthy=True)
        assert health.healthy is True
        assert health.error_count == 0

    async def test_report_unhealthy(self, service: ProviderRoutingService) -> None:
        health = await service.report_health("ep-1", healthy=False)
        assert health.healthy is False
        assert health.error_count == 1

    async def test_get_endpoint_health(self, service: ProviderRoutingService) -> None:
        await service.report_health("ep-1", healthy=True)
        h = service.get_endpoint_health("ep-1")
        assert h is not None
        assert h.healthy is True

    async def test_get_endpoint_health_none(self, service: ProviderRoutingService) -> None:
        assert service.get_endpoint_health("nonexistent") is None


# ---------------------------------------------------------------------------
# Service — Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    async def test_record_success(self, service: ProviderRoutingService) -> None:
        config = ProviderRouteConfig()
        await service.create_route("metrics-route", config)
        m = await service.record_request("metrics-route", success=True, latency_ms=10.0)
        assert m.total_requests == 1
        assert m.successful_requests == 1
        assert m.failed_requests == 0
        assert m.average_latency_ms == 10.0

    async def test_record_failure(self, service: ProviderRoutingService) -> None:
        config = ProviderRouteConfig()
        await service.create_route("metrics-route-2", config)
        m = await service.record_request("metrics-route-2", success=False, latency_ms=5.0)
        assert m.total_requests == 1
        assert m.successful_requests == 0
        assert m.failed_requests == 1

    async def test_get_metrics_none(self, service: ProviderRoutingService) -> None:
        assert service.get_metrics("nonexistent") is None

    async def test_get_all_metrics(self, service: ProviderRoutingService) -> None:
        config = ProviderRouteConfig()
        await service.create_route("m1", config)
        await service.create_route("m2", config)
        await service.record_request("m1", success=True, latency_ms=1.0)
        all_m = service.get_all_metrics()
        assert len(all_m) == 2


# ---------------------------------------------------------------------------
# Service — Failover
# ---------------------------------------------------------------------------


class TestFailover:
    async def test_failover_no_healthy_endpoints_triggers_fallback(
        self,
        service: ProviderRoutingService,
    ) -> None:
        ep = ProviderEndpoint(
            endpoint_id="ep-only", provider_id="p1", url="http://only.example.com"
        )
        config = ProviderRouteConfig(
            load_balancer=LoadBalancerConfig(endpoints=(ep,)),
            failover=FailoverConfig(enabled=True, max_attempts=1, fallback_endpoint_id="ep-only"),
        )
        await service.create_route("f1", config)
        await service.report_health("ep-only", healthy=False)
        with pytest.raises(ProviderEndpointUnavailableError):
            await service.select_route("req-1")

    async def test_failover_exhausts_attempts(
        self,
        service: ProviderRoutingService,
        endpoint_a: ProviderEndpoint,
        endpoint_b: ProviderEndpoint,
    ) -> None:
        config = ProviderRouteConfig(
            load_balancer=LoadBalancerConfig(endpoints=(endpoint_a, endpoint_b)),
            failover=FailoverConfig(enabled=True, max_attempts=1),
        )
        await service.create_route("f2", config)
        await service.report_health("ep-a", healthy=False)
        await service.report_health("ep-b", healthy=False)
        with pytest.raises(ProviderFallbackError):
            await service.failover("f2", "req-1", "ep-a")


# ---------------------------------------------------------------------------
# Service — Audit
# ---------------------------------------------------------------------------


class TestAudit:
    async def test_audit_log(self, service: ProviderRoutingService) -> None:
        await service.create_route("audit-route", ProviderRouteConfig())
        await service.audit_log("audit-route", "test_action", actor="tester")
        # No exception means success — audit events are published internally
        assert True


# ---------------------------------------------------------------------------
# Service — Health Check
# ---------------------------------------------------------------------------


class TestServiceHealthCheck:
    async def test_health_check(self, populated_service: ProviderRoutingService) -> None:
        hc = await populated_service.health_check()
        assert hc["total_routes"] == 1
        assert hc["active_routes"] == 1
        assert hc["total_endpoints"] == 2
        assert hc["healthy_endpoints"] == 2
