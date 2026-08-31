"""Tests for CacheManager (multi-level cache)."""

from __future__ import annotations

import pytest

from eaip.cache.manager import CacheManager
from eaip.cache.models import CacheConfig
from eaip.cache.provider import InMemoryCache


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(config=CacheConfig(max_size_bytes=0, max_entries=1000))


@pytest.fixture
def l2_manager() -> CacheManager:
    l2 = InMemoryCache(max_entries=100, namespace="l2")
    return CacheManager(
        config=CacheConfig(max_size_bytes=0, max_entries=100),
        l2_provider=l2,
    )


class TestCacheManager:
    @pytest.mark.asyncio
    async def test_set_and_get_l1(self, manager: CacheManager) -> None:
        await manager.set("key", b"value")
        result = await manager.get("key")
        assert result == b"value"

    @pytest.mark.asyncio
    async def test_get_miss(self, manager: CacheManager) -> None:
        result = await manager.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, manager: CacheManager) -> None:
        await manager.set("key", b"value")
        assert await manager.delete("key") is True
        assert await manager.get("key") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, manager: CacheManager) -> None:
        assert await manager.delete("nope") is False

    @pytest.mark.asyncio
    async def test_exists(self, manager: CacheManager) -> None:
        await manager.set("key", b"value")
        assert await manager.exists("key") is True
        assert await manager.exists("nope") is False

    @pytest.mark.asyncio
    async def test_clear(self, manager: CacheManager) -> None:
        await manager.set("a", b"1")
        await manager.set("b", b"2")
        count = await manager.clear()
        assert count >= 2
        assert await manager.get("a") is None

    @pytest.mark.asyncio
    async def test_multi_level_l2_populates_l1(self, l2_manager: CacheManager) -> None:
        await l2_manager._l2.set("key", b"from_l2")
        result = await l2_manager.get("key")
        assert result == b"from_l2"
        l1_result = await l2_manager._l1.get("key")
        assert l1_result == b"from_l2"

    @pytest.mark.asyncio
    async def test_get_or_compute_with_factory(self, manager: CacheManager) -> None:
        called = False

        async def factory() -> bytes:
            nonlocal called
            called = True
            return b"computed"

        result = await manager.get_or_compute("key", factory)
        assert result == b"computed"
        assert called is True

        called = False
        result2 = await manager.get_or_compute("key", factory)
        assert result2 == b"computed"
        assert called is False

    @pytest.mark.asyncio
    async def test_get_or_compute_cached(self, manager: CacheManager) -> None:
        async def factory() -> bytes:
            return b"value"

        result = await manager.get_or_compute("key", factory)
        assert result == b"value"

    @pytest.mark.asyncio
    async def test_config_property(self, manager: CacheManager) -> None:
        assert manager.config.default_ttl_seconds == 300

    @pytest.mark.asyncio
    async def test_stats(self, manager: CacheManager) -> None:
        await manager.get("miss1")
        await manager.get("miss2")
        await manager.set("hit", b"x")
        await manager.get("hit")
        stats = await manager.get_stats()
        assert stats.total_misses >= 2

    @pytest.mark.asyncio
    async def test_close(self, manager: CacheManager) -> None:
        await manager.set("a", b"1")
        await manager.close()
        assert await manager.get("a") is None

    @pytest.mark.asyncio
    async def test_ttl_respected(self, manager: CacheManager) -> None:
        await manager.set("key", b"value", ttl_seconds=0)
        result = await manager.get("key")
        assert result is None
