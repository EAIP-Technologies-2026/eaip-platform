"""Tests for :mod:`eaip.datamask.integration`."""

from __future__ import annotations

import asyncio

from eaip.datamask.integration import DataMaskRuntimeModule
from eaip.health.checks import HealthCheck


class _MockHealth:
    def __init__(self) -> None:
        self.registered: list[object] = []

    def register(self, check: object) -> None:
        self.registered.append(check)


class _MockCapabilities:
    def __init__(self) -> None:
        self.registered: list[object] = []

    def register(self, capability: object) -> None:
        self.registered.append(capability)


class _MockPlatform:
    def __init__(self) -> None:
        self._health = _MockHealth()
        self._capabilities = _MockCapabilities()

    @property
    def health(self) -> _MockHealth:
        return self._health

    @property
    def capabilities(self) -> _MockCapabilities:
        return self._capabilities


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


class TestDataMaskRuntimeModule:
    def test_name(self) -> None:
        module = DataMaskRuntimeModule()
        assert module.name == "datamask"

    def test_start_registers_health_check(self) -> None:
        module = DataMaskRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform.health.registered) == 1
        assert isinstance(kernel.platform.health.registered[0], HealthCheck)

    def test_start_registers_capability(self) -> None:
        module = DataMaskRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform.capabilities.registered) == 1

    def test_services_available(self) -> None:
        module = DataMaskRuntimeModule()
        assert module.masking is not None
        assert module.pii is not None
        assert module.anonymization is not None

    def test_health_check_property(self) -> None:
        module = DataMaskRuntimeModule()
        assert module.health_check is not None
        assert module.health_check.name == "datamask"

    def test_stop_does_not_raise(self) -> None:
        module = DataMaskRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        asyncio.run(module.stop(kernel))
