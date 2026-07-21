"""Tests for :mod:`eaip.mesh.load_balancer`."""

from __future__ import annotations

import pytest

from eaip.mesh.exceptions import LoadBalancerError
from eaip.mesh.load_balancer import LoadBalancer
from eaip.mesh.models import RoutingStrategy, ServiceInstance, ServiceStatus


@pytest.fixture
def lb() -> LoadBalancer:
    return LoadBalancer()


@pytest.fixture
def instances() -> list[ServiceInstance]:
    return [
        ServiceInstance(id="s1", name="users", host="10.0.0.1", port=8080, status=ServiceStatus.UP),
        ServiceInstance(id="s2", name="users", host="10.0.0.2", port=8080, status=ServiceStatus.UP),
        ServiceInstance(
            id="s3", name="users", host="10.0.0.3", port=8080, status=ServiceStatus.UP, weight=5
        ),
    ]


class TestLoadBalancer:
    def test_round_robin_cycles(self, lb: LoadBalancer, instances: list[ServiceInstance]) -> None:
        selected = [
            lb.get_next_instance("users", instances, RoutingStrategy.ROUND_ROBIN) for _ in range(5)
        ]
        ids = [s.id for s in selected]
        assert ids[:3] == ["s1", "s2", "s3"]
        assert ids[3:] == ["s1", "s2"]

    def test_random(self, lb: LoadBalancer, instances: list[ServiceInstance]) -> None:
        results = {
            lb.get_next_instance("users", instances, RoutingStrategy.RANDOM).id for _ in range(20)
        }
        assert results == {"s1", "s2", "s3"}

    def test_weighted_distribution(
        self, lb: LoadBalancer, instances: list[ServiceInstance]
    ) -> None:
        selected = [
            lb.get_next_instance("users", instances, RoutingStrategy.WEIGHTED).id
            for _ in range(100)
        ]
        s3_count = selected.count("s3")
        # s3 has weight 5 vs s1/s2 weight 1 — should appear more often
        assert s3_count > 20

    def test_least_connections(self, lb: LoadBalancer, instances: list[ServiceInstance]) -> None:
        lb.update_connections("s1", 10, "users")
        lb.update_connections("s2", 5, "users")
        result = lb.get_next_instance("users", instances, RoutingStrategy.LEAST_CONNECTIONS)
        assert result.id == "s3"

    def test_update_connections_increment(
        self, lb: LoadBalancer, instances: list[ServiceInstance]
    ) -> None:
        lb.get_next_instance("users", instances, RoutingStrategy.ROUND_ROBIN)
        lb.update_connections("s1", 1)
        # After first call, should be on s2; just checking no errors

    def test_update_connections_decrement(
        self, lb: LoadBalancer, instances: list[ServiceInstance]
    ) -> None:
        lb.update_connections("s1", 5, "users")
        lb.update_connections("s1", -5, "users")

    def test_empty_instances(self, lb: LoadBalancer) -> None:
        with pytest.raises(LoadBalancerError):
            lb.get_next_instance("empty", [], RoutingStrategy.ROUND_ROBIN)

    def test_unknown_strategy(self, lb: LoadBalancer, instances: list[ServiceInstance]) -> None:
        with pytest.raises(LoadBalancerError):
            lb.get_next_instance("users", instances, "unknown_strategy")  # type: ignore[arg-type]

    def test_round_robin_with_single_instance(self, lb: LoadBalancer) -> None:
        inst = ServiceInstance(id="s1", name="svc", host="h", port=80, status=ServiceStatus.UP)
        result = lb.get_next_instance("svc", [inst], RoutingStrategy.ROUND_ROBIN)
        assert result.id == "s1"
        result2 = lb.get_next_instance("svc", [inst], RoutingStrategy.ROUND_ROBIN)
        assert result2.id == "s1"
