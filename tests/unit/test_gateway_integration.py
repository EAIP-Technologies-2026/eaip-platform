"""Tests for :mod:`eaip.gateway.integration`."""

from __future__ import annotations

from typing import Any

from eaip.gateway.integration import GatewayRuntimeModule


class _MockHealth:
    def __init__(self) -> None:
        self._checks: dict[str, Any] = {}

    def register(self, check: Any) -> None:
        self._checks[check.name] = check


class _MockPlatform:
    def __init__(self) -> None:
        self.health = _MockHealth()


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


class TestGatewayRuntimeModule:
    async def test_startup_duration_starts_zero(self) -> None:
        module = GatewayRuntimeModule()
        assert module.startup_duration == 0.0

    async def test_start_registers_health_check(self) -> None:
        module = GatewayRuntimeModule()
        kernel: Any = _MockKernel()
        await module.start(kernel)
        assert "gateway" in kernel.platform.health._checks

    async def test_start_installs_default_middlewares(self) -> None:
        module = GatewayRuntimeModule()
        kernel: Any = _MockKernel()
        await module.start(kernel)
        assert len(module.router.pipeline.middlewares) == 5

    async def test_stop_does_not_raise(self) -> None:
        module = GatewayRuntimeModule()
        kernel: Any = _MockKernel()
        await module.start(kernel)
        await module.stop(kernel)

    async def test_router_property(self) -> None:
        module = GatewayRuntimeModule()
        assert module.router is not None
        assert module.router.list_endpoints() == []

    async def test_key_store_property(self) -> None:
        module = GatewayRuntimeModule()
        assert module.key_store is not None
        assert module.key_store.list_keys() == []
