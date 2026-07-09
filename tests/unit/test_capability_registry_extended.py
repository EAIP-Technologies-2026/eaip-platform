"""Extended tests for :mod:`eaip.capabilities.registry` — new API surface."""

from __future__ import annotations

from eaip.capabilities.capability import Capability
from eaip.capabilities.registry import CapabilityRegistry
from eaip.exceptions.domain import DuplicateRegistrationError, NotFoundError


def _cap(name: str = "test.cap") -> Capability:
    return Capability(name=name, title=name, version="1.0.0")


def test_try_get() -> None:
    reg = CapabilityRegistry()
    assert reg.try_get("missing") is None
    c = _cap()
    reg.register(c)
    assert reg.try_get("test.cap") is c


def test_keys() -> None:
    reg = CapabilityRegistry()
    reg.register(_cap("a"))
    reg.register(_cap("b"))
    assert set(reg.keys()) == {"a", "b"}


def test_items() -> None:
    reg = CapabilityRegistry()
    c = _cap("a")
    reg.register(c)
    items = reg.items()
    assert len(items) == 1
    assert items[0] == ("a", c)


def test_clear() -> None:
    reg = CapabilityRegistry()
    reg.register(_cap("a"))
    reg.register(_cap("b"))
    reg.clear()
    assert len(reg) == 0


def test_observe() -> None:
    reg = CapabilityRegistry()
    events = []
    remove = reg.observe(events.append)
    reg.register(_cap("a"))
    assert len(events) == 1
    remove()
    reg.register(_cap("b"))
    assert len(events) == 1  # observer was removed


def test_set_status_replaces() -> None:
    reg = CapabilityRegistry()
    c = _cap("a")
    reg.register(c)
    updated = reg.set_status("a", reg.get("a").status)
    assert updated is not c  # replaced with copy
