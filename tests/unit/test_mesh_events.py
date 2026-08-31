"""Tests for :mod:`eaip.mesh.events`."""

from __future__ import annotations

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
from eaip.mesh.models import RoutingStrategy, ServiceStatus


class TestServiceRegistered:
    def test_create(self) -> None:
        event = ServiceRegistered(service_id="s1", service_name="auth")
        assert event.service_id == "s1"
        assert event.service_name == "auth"
        assert event.event_type == "eaip.mesh.service.registered"

    def test_frozen(self) -> None:
        event = ServiceRegistered(service_id="s1", service_name="auth")
        try:
            event.service_id = "s2"
            raise AssertionError("should be frozen")
        except (ValueError, TypeError):
            pass


class TestServiceUnregistered:
    def test_create(self) -> None:
        event = ServiceUnregistered(service_id="s1", service_name="auth")
        assert event.service_id == "s1"
        assert event.event_type == "eaip.mesh.service.unregistered"


class TestServiceHealthChanged:
    def test_create(self) -> None:
        event = ServiceHealthChanged(
            service_id="s1",
            service_name="auth",
            old_status=ServiceStatus.UP,
            new_status=ServiceStatus.DOWN,
        )
        assert event.old_status is ServiceStatus.UP
        assert event.new_status is ServiceStatus.DOWN
        assert event.event_type == "eaip.mesh.service.health_changed"


class TestRouteCreated:
    def test_create(self) -> None:
        event = RouteCreated(
            route_id="r1",
            name="test-route",
            source_service="auth",
            destination_service="users",
            strategy=RoutingStrategy.ROUND_ROBIN,
        )
        assert event.route_id == "r1"
        assert event.strategy is RoutingStrategy.ROUND_ROBIN
        assert event.event_type == "eaip.mesh.route.created"


class TestRouteUpdated:
    def test_create(self) -> None:
        event = RouteUpdated(
            route_id="r1",
            name="test-route",
            source_service="auth",
            destination_service="users",
            strategy=RoutingStrategy.WEIGHTED,
        )
        assert event.strategy is RoutingStrategy.WEIGHTED
        assert event.event_type == "eaip.mesh.route.updated"


class TestCircuitBreakerTripped:
    def test_create(self) -> None:
        event = CircuitBreakerTripped(service_name="auth", failure_count=5)
        assert event.service_name == "auth"
        assert event.failure_count == 5
        assert event.event_type == "eaip.mesh.circuit_breaker.tripped"


class TestCircuitBreakerReset:
    def test_create(self) -> None:
        event = CircuitBreakerReset(service_name="auth")
        assert event.service_name == "auth"
        assert event.event_type == "eaip.mesh.circuit_breaker.reset"


class TestLoadBalanced:
    def test_create(self) -> None:
        event = LoadBalanced(
            service_name="auth",
            strategy=RoutingStrategy.ROUND_ROBIN,
            selected_instance_id="s1",
        )
        assert event.service_name == "auth"
        assert event.selected_instance_id == "s1"
        assert event.event_type == "eaip.mesh.load_balancer.balanced"
