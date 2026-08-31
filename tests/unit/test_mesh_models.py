"""Tests for :mod:`eaip.mesh.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.mesh.models import (
    LoadBalancerState,
    MeshConfig,
    RoutingStrategy,
    ServiceInstance,
    ServiceRoute,
    ServiceStatus,
)


class TestServiceStatus:
    def test_values(self) -> None:
        assert ServiceStatus.UP == "up"
        assert ServiceStatus.DOWN == "down"
        assert ServiceStatus.UNKNOWN == "unknown"

    def test_is_str_enum(self) -> None:
        assert issubclass(ServiceStatus, str)


class TestRoutingStrategy:
    def test_values(self) -> None:
        assert RoutingStrategy.ROUND_ROBIN == "round_robin"
        assert RoutingStrategy.LEAST_CONNECTIONS == "least_connections"
        assert RoutingStrategy.RANDOM == "random"
        assert RoutingStrategy.WEIGHTED == "weighted"
        assert RoutingStrategy.HEALTH_BASED == "health_based"


class TestServiceInstance:
    def test_minimal(self) -> None:
        inst = ServiceInstance(id="svc-1", name="auth", host="10.0.0.1", port=8080)
        assert inst.id == "svc-1"
        assert inst.name == "auth"
        assert inst.host == "10.0.0.1"
        assert inst.port == 8080
        assert inst.protocol == "http"
        assert inst.status is ServiceStatus.UNKNOWN
        assert inst.weight == 1

    def test_frozen(self) -> None:
        inst = ServiceInstance(id="svc-1", name="auth", host="10.0.0.1", port=8080)
        with pytest.raises(ValidationError):
            inst.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ServiceInstance(
                id="svc-1",
                name="auth",
                host="10.0.0.1",
                port=8080,
                unknown=True,
            )

    def test_all_fields(self) -> None:
        ts = datetime.now(UTC)
        inst = ServiceInstance(
            id="svc-1",
            name="auth",
            version="2.0.0",
            host="10.0.0.1",
            port=443,
            protocol="https",
            status=ServiceStatus.UP,
            health_endpoint="/healthz",
            metadata={"env": "prod"},
            tags=("critical", "internal"),
            registered_at=ts,
            last_heartbeat=ts,
            weight=5,
        )
        assert inst.version == "2.0.0"
        assert inst.protocol == "https"
        assert inst.status is ServiceStatus.UP
        assert inst.health_endpoint == "/healthz"
        assert inst.metadata == {"env": "prod"}
        assert inst.tags == ("critical", "internal")
        assert inst.registered_at == ts
        assert inst.last_heartbeat == ts
        assert inst.weight == 5

    def test_port_range(self) -> None:
        with pytest.raises(ValidationError):
            ServiceInstance(id="s", name="n", host="h", port=0)
        with pytest.raises(ValidationError):
            ServiceInstance(id="s", name="n", host="h", port=65536)

    def test_weight_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            ServiceInstance(id="s", name="n", host="h", port=80, weight=0)


class TestServiceRoute:
    def test_minimal(self) -> None:
        route = ServiceRoute(
            id="r-1",
            name="auth-to-users",
            source_service="auth",
            destination_service="users",
        )
        assert route.routing_strategy is RoutingStrategy.ROUND_ROBIN
        assert route.conditions == ()
        assert route.enabled is True
        assert route.timeout_seconds == 30.0

    def test_frozen(self) -> None:
        route = ServiceRoute(
            id="r-1",
            name="test",
            source_service="a",
            destination_service="b",
        )
        with pytest.raises(ValidationError):
            route.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ServiceRoute(
                id="r-1",
                name="test",
                source_service="a",
                destination_service="b",
                unknown=True,
            )

    def test_all_fields(self) -> None:
        route = ServiceRoute(
            id="r-1",
            name="Full Route",
            source_service="auth",
            destination_service="users",
            routing_strategy=RoutingStrategy.WEIGHTED,
            conditions=("region == us-east", "env == prod"),
            fallback_service="users-backup",
            timeout_seconds=60.0,
            retry_count=5,
            circuit_breaker_config={"failure_threshold": 3},
            enabled=False,
            metadata={"owner": "team-a"},
        )
        assert route.routing_strategy is RoutingStrategy.WEIGHTED
        assert route.conditions == ("region == us-east", "env == prod")
        assert route.fallback_service == "users-backup"
        assert route.timeout_seconds == 60.0
        assert route.retry_count == 5
        assert route.circuit_breaker_config == {"failure_threshold": 3}
        assert route.enabled is False
        assert route.metadata == {"owner": "team-a"}

    def test_all_strategies(self) -> None:
        for s in RoutingStrategy:
            route = ServiceRoute(
                id=f"r-{s.value}",
                name=s.value,
                source_service="a",
                destination_service="b",
                routing_strategy=s,
            )
            assert route.routing_strategy is s


class TestLoadBalancerState:
    def test_minimal(self) -> None:
        state = LoadBalancerState(service_name="auth")
        assert state.current_index == 0
        assert state.active_connections == {}
        assert state.strategy is RoutingStrategy.ROUND_ROBIN
        assert state.last_distribution is None

    def test_frozen(self) -> None:
        state = LoadBalancerState(service_name="auth")
        with pytest.raises(ValidationError):
            state.service_name = "changed"


class TestMeshConfig:
    def test_defaults(self) -> None:
        cfg = MeshConfig()
        assert cfg.heartbeat_interval_seconds == 15.0
        assert cfg.health_check_timeout == 5.0
        assert cfg.circuit_breaker_threshold == 5
        assert cfg.max_retries == 3
        assert cfg.enable_tracing is False
        assert cfg.metrics_port == 9090

    def test_custom(self) -> None:
        cfg = MeshConfig(
            heartbeat_interval_seconds=30.0,
            health_check_timeout=10.0,
            circuit_breaker_threshold=10,
            max_retries=5,
            enable_tracing=True,
            metrics_port=9091,
        )
        assert cfg.heartbeat_interval_seconds == 30.0
        assert cfg.health_check_timeout == 10.0
        assert cfg.circuit_breaker_threshold == 10
        assert cfg.max_retries == 5
        assert cfg.enable_tracing is True
        assert cfg.metrics_port == 9091

    def test_frozen(self) -> None:
        cfg = MeshConfig()
        with pytest.raises(ValidationError):
            cfg.max_retries = 10

    def test_validation(self) -> None:
        with pytest.raises(ValidationError):
            MeshConfig(heartbeat_interval_seconds=0)
        with pytest.raises(ValidationError):
            MeshConfig(metrics_port=80)
