"""Tests for :mod:`eaip.capabilities.events`."""

from __future__ import annotations

from eaip.capabilities.events import (
    CapabilityDeprecated,
    CapabilityDisabled,
    CapabilityEnabled,
    CapabilityHealthChanged,
    CapabilityRegistered,
    CapabilityUpgraded,
)
from eaip.events.event import DomainEvent


def _assert_is_domain_event(evt: object) -> None:
    assert isinstance(evt, DomainEvent)


def test_capability_registered() -> None:
    evt = CapabilityRegistered(name="test.cap", version="1.0.0")
    _assert_is_domain_event(evt)
    assert evt.name == "test.cap"
    assert evt.version == "1.0.0"
    assert evt.contract_version is None

    evt2 = CapabilityRegistered(name="test.cap", version="1.0.0", contract_version="1.0.0")
    assert evt2.contract_version == "1.0.0"


def test_capability_enabled() -> None:
    evt = CapabilityEnabled(name="test.cap", version="1.0.0")
    _assert_is_domain_event(evt)
    assert evt.name == "test.cap"


def test_capability_disabled() -> None:
    evt = CapabilityDisabled(name="test.cap", version="1.0.0")
    _assert_is_domain_event(evt)
    assert evt.name == "test.cap"


def test_capability_deprecated() -> None:
    evt = CapabilityDeprecated(name="test.cap", version="1.0.0")
    _assert_is_domain_event(evt)
    assert evt.name == "test.cap"


def test_capability_upgraded() -> None:
    evt = CapabilityUpgraded(name="test.cap", previous_version="1.0.0", new_version="2.0.0")
    _assert_is_domain_event(evt)
    assert evt.previous_version == "1.0.0"
    assert evt.new_version == "2.0.0"


def test_capability_health_changed() -> None:
    evt = CapabilityHealthChanged(name="test.cap", status="degraded", message="disabled")
    _assert_is_domain_event(evt)
    assert evt.status == "degraded"
    assert evt.message == "disabled"
