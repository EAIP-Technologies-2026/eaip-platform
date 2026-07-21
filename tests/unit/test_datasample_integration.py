"""Tests for :mod:`eaip.datasample.integration`."""

from __future__ import annotations

import asyncio

from eaip.datasample.integration import DataSampleRuntimeModule
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


class TestDataSampleRuntimeModule:
    def test_name(self) -> None:
        module = DataSampleRuntimeModule()
        assert module.name == "datasample"

    def test_start_registers_health_check(self) -> None:
        module = DataSampleRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform.health.registered) == 1
        assert isinstance(kernel.platform.health.registered[0], HealthCheck)

    def test_start_registers_capability(self) -> None:
        module = DataSampleRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform.capabilities.registered) == 1

    def test_sampler_available(self) -> None:
        module = DataSampleRuntimeModule()
        assert module.sampler is not None

    def test_health_check_property(self) -> None:
        module = DataSampleRuntimeModule()
        assert module.health_check is not None
        assert module.health_check.name == "datasample"

    def test_stop_does_not_raise(self) -> None:
        module = DataSampleRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        asyncio.run(module.stop(kernel))
