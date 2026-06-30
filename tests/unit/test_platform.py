"""Tests for :mod:`eaip.platform` and :mod:`eaip.application`."""

from __future__ import annotations

import pytest

from eaip.application import build_platform
from eaip.dependency_injection import Container
from eaip.events import EventBus
from eaip.health import HealthReporter, HealthStatus
from eaip.lifecycle import LifecyclePhase
from eaip.platform import PlatformBuilder
from eaip.ports.clock import ClockPort
from eaip.ports.id_generator import IdGeneratorPort
from eaip.ports.secret_provider import SecretProviderPort


def test_build_platform_minimal() -> None:
    p = build_platform(configure_logging=False)
    assert p.name
    assert p.version
    assert p.phase is LifecyclePhase.CREATED


def test_default_ports_wired_into_container() -> None:
    p = build_platform(configure_logging=False)
    assert p.container.resolve(ClockPort) is not None  # type: ignore[type-abstract]
    assert p.container.resolve(IdGeneratorPort) is not None  # type: ignore[type-abstract]
    assert p.container.resolve(SecretProviderPort) is not None  # type: ignore[type-abstract]


def test_subsystems_available_via_container() -> None:
    p = build_platform(configure_logging=False)
    assert isinstance(p.container.resolve(EventBus), EventBus)
    assert isinstance(p.container.resolve(HealthReporter), HealthReporter)


@pytest.mark.asyncio
async def test_lifecycle_via_context_manager() -> None:
    p = build_platform(configure_logging=False)
    async with p:
        assert p.phase is LifecyclePhase.RUNNING
        report = await p.health.report()
        assert report.status is HealthStatus.HEALTHY
    assert p.phase is LifecyclePhase.STOPPED


@pytest.mark.asyncio
async def test_builder_accepts_custom_container() -> None:
    c = Container()
    p = PlatformBuilder().with_container(c).build()
    # Builder injects the standard subsystems into the supplied container.
    assert c.has(EventBus)
    assert c.has(HealthReporter)
    assert p.container is c


@pytest.mark.asyncio
async def test_platform_starts_and_stops_independently() -> None:
    p = build_platform(configure_logging=False)
    await p.start()
    assert p.phase is LifecyclePhase.RUNNING
    await p.stop()
    assert p.phase is LifecyclePhase.STOPPED
