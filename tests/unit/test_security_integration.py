"""Tests for :mod:`eaip.security.integration`."""

from __future__ import annotations

import asyncio

from eaip.health.checks import HealthCheck
from eaip.security.integration import SecurityRuntimeModule


class _MockHealth:
    def __init__(self) -> None:
        self.registered: list[object] = []

    def register(self, check: object) -> None:
        self.registered.append(check)


class _MockPlatform:
    def __init__(self) -> None:
        self._health = _MockHealth()

    @property
    def health(self) -> _MockHealth:
        return self._health


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


class TestSecurityRuntimeModule:
    def test_name(self) -> None:
        module = SecurityRuntimeModule()
        assert module.name == "security"

    def test_start_registers_health_check(self) -> None:
        module = SecurityRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform.health.registered) == 1
        assert isinstance(kernel.platform.health.registered[0], HealthCheck)

    def test_start_services_available(self) -> None:
        module = SecurityRuntimeModule()
        assert module.vault is not None
        assert module.crypto is not None
        assert module.cert_manager is not None
        assert module.compliance is not None

    def test_health_check_property(self) -> None:
        module = SecurityRuntimeModule()
        assert module.health_check is not None
        assert module.health_check.name == "security"

    def test_stop_does_not_raise(self) -> None:
        module = SecurityRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        asyncio.run(module.stop(kernel))
