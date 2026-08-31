"""Tests for CacheHealthCheck."""

from __future__ import annotations

import pytest

from eaip.cache.health import CacheHealthCheck
from eaip.cache.manager import CacheManager
from eaip.cache.models import CacheConfig
from eaip.cache.provider import InMemoryCache
from eaip.health.checks import HealthStatus


class TestCacheHealthCheck:
    @pytest.mark.asyncio
    async def test_healthy_with_provider(self) -> None:
        provider = InMemoryCache(namespace="test")
        check = CacheHealthCheck(provider=provider)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_healthy_with_manager(self) -> None:
        mgr = CacheManager()
        check = CacheHealthCheck(manager=mgr)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_unhealthy_no_provider(self) -> None:
        check = CacheHealthCheck()
        report = await check.check()
        assert report.status is HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_degraded_low_hit_ratio(self) -> None:
        mgr = CacheManager(config=CacheConfig(max_size_bytes=0, max_entries=1000))
        for _ in range(200):
            await mgr.get("miss")
        report = await mgr._health_check.check() if hasattr(mgr, "_health_check") else None

        check = CacheHealthCheck(manager=mgr)
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_healthy_after_hits(self) -> None:
        mgr = CacheManager()
        await mgr.set("k", b"v")
        for _ in range(10):
            await mgr.get("k")
        check = CacheHealthCheck(manager=mgr)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
