"""Tests for :mod:`eaip.registry.service_registry`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.exceptions.domain import DuplicateRegistrationError, NotFoundError
from eaip.registry.service_registry import ServiceInstance, ServiceRegistry, ServiceStatus


def test_register_and_get() -> None:
    reg = ServiceRegistry()
    inst = reg.register("my_service", object(), metadata={"version": "1.0"})
    assert isinstance(inst, ServiceInstance)
    assert inst.service_type == "my_service"
    assert inst.status is ServiceStatus.REGISTERED
    assert inst.metadata == {"version": "1.0"}

    retrieved = reg.get("my_service")
    assert retrieved is inst


def test_try_get_missing() -> None:
    reg = ServiceRegistry()
    assert reg.try_get("nonexistent") is None


def test_get_missing_raises_not_found() -> None:
    reg = ServiceRegistry()
    with pytest.raises(NotFoundError):
        reg.get("nonexistent")


def test_has() -> None:
    reg = ServiceRegistry()
    assert not reg.has("svc")
    reg.register("svc", object())
    assert reg.has("svc")


def test_contains() -> None:
    reg = ServiceRegistry()
    reg.register("svc", object())
    assert "svc" in reg


def test_all() -> None:
    reg = ServiceRegistry()
    reg.register("a", object())
    reg.register("b", object())
    assert len(reg.all()) == 2


def test_len() -> None:
    reg = ServiceRegistry()
    assert len(reg) == 0
    reg.register("a", object())
    assert len(reg) == 1


def test_count() -> None:
    reg = ServiceRegistry()
    assert reg.count == 0
    reg.register("a", object())
    assert reg.count == 1


def test_unregister() -> None:
    reg = ServiceRegistry()
    reg.register("svc", object())
    assert reg.unregister("svc") is True
    assert reg.unregister("svc") is False


def test_replace() -> None:
    reg = ServiceRegistry()
    obj1 = object()
    obj2 = object()
    reg.register("svc", obj1)
    with pytest.raises(DuplicateRegistrationError):
        reg.register("svc", obj2)  # replace not allowed by default
    reg.register("svc", obj2, replace=True)
    assert reg.get("svc").instance is obj2


def test_set_status() -> None:
    reg = ServiceRegistry()
    reg.register("svc", object())
    inst = reg.set_status("svc", ServiceStatus.RUNNING)
    assert inst.status is ServiceStatus.RUNNING
    assert reg.get("svc").status is ServiceStatus.RUNNING


def test_set_status_missing_raises() -> None:
    reg = ServiceRegistry()
    with pytest.raises(NotFoundError):
        reg.set_status("nonexistent", ServiceStatus.RUNNING)


def test_observe() -> None:
    reg = ServiceRegistry()
    events = []
    remove = reg.observe(events.append)
    reg.register("svc", object())
    reg.unregister("svc")
    remove()
    reg.register("svc2", object())
    assert len(events) == 2


def test_custom_registered_at() -> None:
    ts = datetime(2025, 1, 1, tzinfo=UTC)
    inst = ServiceInstance("svc", object(), registered_at=ts)
    assert inst.registered_at is ts


def test_service_status_values() -> None:
    assert ServiceStatus.REGISTERED.value == "registered"
    assert ServiceStatus.RUNNING.value == "running"
    assert ServiceStatus.STOPPED.value == "stopped"
    assert ServiceStatus.FAILED.value == "failed"
