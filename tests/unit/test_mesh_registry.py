"""Tests for :mod:`eaip.mesh.registry`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.mesh.exceptions import NoHealthyInstanceError, ServiceNotFoundError
from eaip.mesh.models import ServiceInstance, ServiceStatus
from eaip.mesh.registry import ServiceRegistry


@pytest.fixture
def registry() -> ServiceRegistry:
    return ServiceRegistry()


@pytest.fixture
def instance() -> ServiceInstance:
    return ServiceInstance(
        id="svc-1",
        name="auth",
        host="10.0.0.1",
        port=8080,
        status=ServiceStatus.UP,
    )


class TestServiceRegistry:
    def test_register(self, registry: ServiceRegistry, instance: ServiceInstance) -> None:
        result = registry.register(instance)
        assert result.id == instance.id
        assert registry.get_instance("svc-1") == instance

    def test_register_twice_overwrites(
        self, registry: ServiceRegistry, instance: ServiceInstance
    ) -> None:
        registry.register(instance)
        updated = instance.model_copy(update={"version": "2.0.0"})
        registry.register(updated)
        assert registry.get_instance("svc-1").version == "2.0.0"

    def test_unregister(self, registry: ServiceRegistry, instance: ServiceInstance) -> None:
        registry.register(instance)
        registry.unregister("svc-1")
        with pytest.raises(ServiceNotFoundError):
            registry.get_instance("svc-1")

    def test_unregister_not_found(self, registry: ServiceRegistry) -> None:
        with pytest.raises(ServiceNotFoundError):
            registry.unregister("nonexistent")

    def test_get_instance_not_found(self, registry: ServiceRegistry) -> None:
        with pytest.raises(ServiceNotFoundError):
            registry.get_instance("nonexistent")

    def test_list_instances_all(self, registry: ServiceRegistry) -> None:
        i1 = ServiceInstance(id="s1", name="auth", host="h1", port=80)
        i2 = ServiceInstance(id="s2", name="auth", host="h2", port=80)
        i3 = ServiceInstance(id="s3", name="users", host="h3", port=80)
        registry.register(i1)
        registry.register(i2)
        registry.register(i3)
        all_instances = registry.list_instances()
        assert len(all_instances) == 3

    def test_list_instances_by_name(self, registry: ServiceRegistry) -> None:
        i1 = ServiceInstance(id="s1", name="auth", host="h1", port=80)
        i2 = ServiceInstance(id="s2", name="users", host="h2", port=80)
        registry.register(i1)
        registry.register(i2)
        auth_instances = registry.list_instances("auth")
        assert len(auth_instances) == 1
        assert auth_instances[0].id == "s1"

    def test_heartbeat_updates_timestamp_and_status(self, registry: ServiceRegistry) -> None:
        inst = ServiceInstance(
            id="svc-1",
            name="auth",
            host="10.0.0.1",
            port=8080,
            status=ServiceStatus.UNKNOWN,
        )
        registry.register(inst)
        result = registry.heartbeat("svc-1")
        assert result.status is ServiceStatus.UP
        assert result.last_heartbeat > inst.registered_at

    def test_heartbeat_not_found(self, registry: ServiceRegistry) -> None:
        with pytest.raises(ServiceNotFoundError):
            registry.heartbeat("nonexistent")

    def test_check_expired(self, registry: ServiceRegistry) -> None:
        old_ts = datetime(2020, 1, 1, tzinfo=UTC)
        inst = ServiceInstance(
            id="svc-1",
            name="auth",
            host="10.0.0.1",
            port=8080,
            last_heartbeat=old_ts,
            status=ServiceStatus.UP,
        )
        registry.register(inst)
        expired = registry.check_expired(timeout_seconds=10.0)
        assert len(expired) == 1
        assert expired[0].id == "svc-1"
        assert registry.get_instance("svc-1").status is ServiceStatus.DOWN

    def test_check_expired_no_expired(self, registry: ServiceRegistry) -> None:
        inst = ServiceInstance(
            id="svc-1",
            name="auth",
            host="10.0.0.1",
            port=8080,
            status=ServiceStatus.UP,
        )
        registry.register(inst)
        expired = registry.check_expired(timeout_seconds=3600.0)
        assert expired == []

    def test_get_healthy_instances(self, registry: ServiceRegistry) -> None:
        i1 = ServiceInstance(id="s1", name="auth", host="h1", port=80, status=ServiceStatus.UP)
        i2 = ServiceInstance(id="s2", name="auth", host="h2", port=80, status=ServiceStatus.DOWN)
        registry.register(i1)
        registry.register(i2)
        healthy = registry.get_healthy_instances("auth")
        assert len(healthy) == 1
        assert healthy[0].id == "s1"

    def test_get_healthy_instances_none(self, registry: ServiceRegistry) -> None:
        with pytest.raises(NoHealthyInstanceError):
            registry.get_healthy_instances("nonexistent")

    def test_list_services(self, registry: ServiceRegistry) -> None:
        registry.register(ServiceInstance(id="s1", name="auth", host="h1", port=80))
        registry.register(ServiceInstance(id="s2", name="users", host="h2", port=80))
        services = registry.list_services()
        assert sorted(services) == ["auth", "users"]

    def test_event_bus_publish(self) -> None:
        events: list[object] = []

        class FakeBus:
            def publish(self, event: object) -> None:
                events.append(event)

        reg = ServiceRegistry(event_bus=FakeBus())
        inst = ServiceInstance(id="svc-1", name="auth", host="h", port=80)
        reg.register(inst)
        reg.unregister("svc-1")
        assert len(events) == 2
        assert events[0].event_type == "eaip.mesh.service.registered"
        assert events[1].event_type == "eaip.mesh.service.unregistered"
