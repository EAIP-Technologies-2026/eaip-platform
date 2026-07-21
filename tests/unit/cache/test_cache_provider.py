"""Tests for InMemoryCache and NullCache."""

from __future__ import annotations

import pytest

from eaip.cache.provider import InMemoryCache, NullCache


class TestNullCache:
    @pytest.mark.asyncio
    async def test_get_returns_none(self) -> None:
        cache = NullCache()
        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_does_not_store(self) -> None:
        cache = NullCache()
        await cache.set("key", b"value")
        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_returns_false(self) -> None:
        cache = NullCache()
        result = await cache.delete("key")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_false(self) -> None:
        cache = NullCache()
        result = await cache.exists("key")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_returns_zero(self) -> None:
        cache = NullCache()
        result = await cache.clear()
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_stats(self) -> None:
        cache = NullCache()
        stats = await cache.get_stats()
        assert stats.total_entries == 0

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        cache = NullCache()
        await cache.close()


class TestInMemoryCache:
    @pytest.mark.asyncio
    async def test_set_and_get(self) -> None:
        cache = InMemoryCache()
        await cache.set("key1", b"value1")
        result = await cache.get("key1")
        assert result == b"value1"

    @pytest.mark.asyncio
    async def test_get_miss(self) -> None:
        cache = InMemoryCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self) -> None:
        cache = InMemoryCache()
        await cache.set("key", b"value")
        deleted = await cache.delete("key")
        assert deleted is True
        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        cache = InMemoryCache()
        deleted = await cache.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists(self) -> None:
        cache = InMemoryCache()
        await cache.set("key", b"value")
        assert await cache.exists("key") is True
        assert await cache.exists("other") is False

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        cache = InMemoryCache()
        await cache.set("a", b"1")
        await cache.set("b", b"2")
        count = await cache.clear()
        assert count == 2
        assert await cache.get("a") is None

    @pytest.mark.asyncio
    async def test_ttl_expiry(self) -> None:
        cache = InMemoryCache()
        await cache.set("key", b"value", ttl_seconds=0)
        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self) -> None:
        cache = InMemoryCache(max_entries=2)
        await cache.set("a", b"1")
        await cache.set("b", b"2")
        await cache.set("c", b"3")
        assert await cache.get("a") is None
        assert await cache.get("c") == b"3"

    @pytest.mark.asyncio
    async def test_size_eviction(self) -> None:
        cache = InMemoryCache(max_size_bytes=10)
        await cache.set("a", b"0123456789")
        await cache.set("b", b"0123456789")
        assert await cache.get("a") is None
        assert await cache.get("b") == b"0123456789"

    @pytest.mark.asyncio
    async def test_get_stats(self) -> None:
        cache = InMemoryCache()
        await cache.set("a", b"1")
        await cache.get("a")
        await cache.get("miss")
        stats = await cache.get_stats()
        assert stats.total_entries == 1
        assert stats.total_hits == 1
        assert stats.total_misses == 1
        assert stats.hit_ratio == 0.5

    @pytest.mark.asyncio
    async def test_get_updates_hits(self) -> None:
        cache = InMemoryCache()
        await cache.set("key", b"value")
        await cache.get("key")
        await cache.get("key")
        stats = await cache.get_stats()
        assert stats.total_hits == 2

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        cache = InMemoryCache()
        await cache.set("a", b"1")
        await cache.close()
        assert await cache.get("a") is None
