from __future__ import annotations

import asyncio

import httpx
import pytest

from eaip.health.checks import HealthStatus
from eaip.providers.health import ProviderHealthCheck, ProviderHealthMonitor
from eaip.providers.models import ProviderInstance, ProviderStatus
from eaip.providers.registry import ProviderRegistry


class _HealthyTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b'{"ok": true}', request=request)


class _UnhealthyTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, content=b"Service Unavailable", request=request)


class TestProviderHealthCheck:
    def test_no_providers_healthy(self) -> None:
        registry = ProviderRegistry()
        check = ProviderHealthCheck(registry)
        report = asyncio.run(check.check())
        assert report.status is HealthStatus.HEALTHY

    def test_all_healthy(self) -> None:
        registry = ProviderRegistry()
        inst = ProviderInstance(name="test", provider_type="test", endpoint="http://test",
                                 status=ProviderStatus.AVAILABLE)
        registry.register(inst)

        check = ProviderHealthCheck(registry)

        async def _probe(inst: ProviderInstance) -> bool:
            return True

        check._probe = _probe  # type: ignore[method-assign]
        report = asyncio.run(check.check())
        assert report.status is HealthStatus.HEALTHY

    def test_some_unhealthy_degraded(self) -> None:
        registry = ProviderRegistry()
        registry.register(ProviderInstance(name="a", provider_type="t", endpoint="http://a"))
        registry.register(ProviderInstance(name="b", provider_type="t", endpoint="http://b"))

        check = ProviderHealthCheck(registry)
        probe_results = {"a": True, "b": False}

        async def _probe(inst: ProviderInstance) -> bool:
            return probe_results.get(inst.name, False)

        check._probe = _probe  # type: ignore[method-assign]
        report = asyncio.run(check.check())
        assert report.status is HealthStatus.DEGRADED

    def test_all_unhealthy(self) -> None:
        registry = ProviderRegistry()
        registry.register(ProviderInstance(name="a", provider_type="t", endpoint="http://a"))

        check = ProviderHealthCheck(registry)

        async def _probe(inst: ProviderInstance) -> bool:
            return False

        check._probe = _probe  # type: ignore[method-assign]
        report = asyncio.run(check.check())
        assert report.status is HealthStatus.UNHEALTHY

    def test_updates_provider_status(self) -> None:
        registry = ProviderRegistry()
        inst = ProviderInstance(name="test", provider_type="t", endpoint="http://test",
                                 status=ProviderStatus.UNAVAILABLE)
        registry.register(inst)

        check = ProviderHealthCheck(registry)

        async def _probe(inst: ProviderInstance) -> bool:
            return True

        check._probe = _probe  # type: ignore[method-assign]
        asyncio.run(check.check())
        updated = registry.get("test")
        assert updated.status is ProviderStatus.AVAILABLE


class TestProviderHealthMonitor:
    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        registry = ProviderRegistry()
        monitor = ProviderHealthMonitor(registry, interval_seconds=0.1)
        await monitor.start()
        assert monitor._task is not None
        assert not monitor._task.done()
        await asyncio.sleep(0.15)
        await monitor.stop()
        assert monitor._task is None
