"""Tests for :mod:`eaip.capabilities.health`."""

from __future__ import annotations

import asyncio

from eaip.capabilities.capability import Capability
from eaip.capabilities.health import CapabilityHealthCheck
from eaip.capabilities.registry import CapabilityRegistry
from eaip.health.checks import HealthStatus


def test_no_capabilities() -> None:
    reg = CapabilityRegistry()
    check = CapabilityHealthCheck(reg)
    report = asyncio.run(check.check())
    assert report.status is HealthStatus.HEALTHY
    assert "no capabilities" in report.message


def test_all_enabled() -> None:
    reg = CapabilityRegistry()
    c = Capability(name="test", title="Test", version="1.0.0")
    reg.register(c)
    reg.enable("test")
    check = CapabilityHealthCheck(reg)
    report = asyncio.run(check.check())
    assert report.status is HealthStatus.HEALTHY
    assert "healthy" in report.message


def test_degraded_with_disabled() -> None:
    reg = CapabilityRegistry()
    reg.register(Capability(name="a", title="A", version="1.0.0"))
    reg.disable("a")
    check = CapabilityHealthCheck(reg)
    report = asyncio.run(check.check())
    assert report.status is HealthStatus.DEGRADED


def test_degraded_with_deprecated() -> None:
    reg = CapabilityRegistry()
    reg.register(Capability(name="a", title="A", version="1.0.0"))
    reg.deprecate("a")
    check = CapabilityHealthCheck(reg)
    report = asyncio.run(check.check())
    assert report.status is HealthStatus.DEGRADED


def test_cycle_unhealthy() -> None:
    reg = CapabilityRegistry()
    from eaip.capabilities.capability import CapabilityDependency

    a = Capability(
        name="a",
        title="A",
        version="1.0.0",
        depends_on=(CapabilityDependency(name="b"),),
    )
    b = Capability(
        name="b",
        title="B",
        version="1.0.0",
        depends_on=(CapabilityDependency(name="a"),),
    )
    reg.register(a)
    reg.register(b)
    check = CapabilityHealthCheck(reg)
    report = asyncio.run(check.check())
    assert report.status is HealthStatus.UNHEALTHY
