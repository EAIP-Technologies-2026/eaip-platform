"""Tests for :mod:`eaip.capabilities`."""

from __future__ import annotations

import pytest

from eaip.capabilities import Capability, CapabilityRegistry, CapabilityStatus
from eaip.exceptions.domain import DuplicateRegistrationError, NotFoundError


def _cap(name: str = "agent.run") -> Capability:
    return Capability(name=name, title="Agent Run", version="1.0.0")


def test_register_and_get() -> None:
    reg = CapabilityRegistry()
    c = _cap()
    reg.register(c)
    assert reg.get(c.name) == c


def test_status_transitions() -> None:
    reg = CapabilityRegistry()
    c = _cap()
    reg.register(c)
    reg.enable(c.name)
    assert reg.get(c.name).status is CapabilityStatus.ENABLED
    reg.disable(c.name)
    assert reg.get(c.name).status is CapabilityStatus.DISABLED
    reg.deprecate(c.name)
    assert reg.get(c.name).status is CapabilityStatus.DEPRECATED


def test_duplicate_raises() -> None:
    reg = CapabilityRegistry()
    reg.register(_cap())
    with pytest.raises(DuplicateRegistrationError):
        reg.register(_cap())


def test_missing_raises_not_found() -> None:
    reg = CapabilityRegistry()
    with pytest.raises(NotFoundError):
        reg.set_status("nope", CapabilityStatus.ENABLED)


def test_enabled_filter() -> None:
    reg = CapabilityRegistry()
    reg.register(_cap("a"))
    reg.register(_cap("b"))
    reg.enable("a")
    assert [c.name for c in reg.enabled()] == ["a"]


def test_metadata_translation() -> None:
    md = _cap().to_metadata()
    assert md.kind.value == "capability"
    assert md.name == "agent.run"
