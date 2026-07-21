"""Tests for :mod:`eaip.tenants.integration`."""

from __future__ import annotations

from typing import Any

import pytest

from eaip.tenants.health import TenantHealthCheck
from eaip.tenants.integration import TenantRuntimeModule


class _MockHealthReporter:
    def __init__(self) -> None:
        self.registered: list[Any] = []

    def register(self, check: Any) -> None:
        self.registered.append(check)


class _MockPlatform:
    def __init__(self) -> None:
        self.health = _MockHealthReporter()


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


@pytest.fixture
def kernel() -> _MockKernel:
    return _MockKernel()


class TestTenantRuntimeModule:
    def test_name(self) -> None:
        module = TenantRuntimeModule()
        assert module.name == "tenants"

    def test_started_defaults_false(self) -> None:
        module = TenantRuntimeModule()
        assert module.started is False

    async def test_start_registers_health_check(self, kernel: _MockKernel) -> None:
        module = TenantRuntimeModule()
        await module.start(kernel)
        assert module.started is True
        assert len(kernel.platform.health.registered) == 1

    async def test_start_registers_tenant_health_check(self, kernel: _MockKernel) -> None:
        module = TenantRuntimeModule()
        await module.start(kernel)
        registered = kernel.platform.health.registered[0]
        assert isinstance(registered, TenantHealthCheck)

    async def test_stop_sets_started_false(self, kernel: _MockKernel) -> None:
        module = TenantRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)
        assert module.started is False

    async def test_custom_health_check(self, kernel: _MockKernel) -> None:
        custom = TenantHealthCheck()
        module = TenantRuntimeModule(health_check=custom)
        await module.start(kernel)
        registered = kernel.platform.health.registered[0]
        assert registered is custom
