"""Tests for :mod:`eaip.apiext.caching`."""

from __future__ import annotations

import pytest

from eaip.apiext.caching import ResponseCache


class TestResponseCache:
    @pytest.fixture
    def cache(self) -> ResponseCache:
        return ResponseCache(max_size=10, default_ttl=60.0)

    async def test_get_miss(self, cache: ResponseCache) -> None:
        result = await cache.get("nonexistent")
        assert result is None

    async def test_set_and_get(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "hello"}, ttl=60.0)
        entry = await cache.get("key1")
        assert entry is not None
        assert entry.response_body == {"data": "hello"}
        assert entry.hit_count >= 0

    async def test_get_increments_hit_count(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "hello"}, ttl=60.0)
        entry1 = await cache.get("key1")
        assert entry1 is not None
        hit1 = entry1.hit_count
        entry2 = await cache.get("key1")
        assert entry2 is not None
        assert entry2.hit_count == hit1 + 1

    async def test_get_expired_entry(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "hello"}, ttl=-1.0)
        result = await cache.get("key1")
        assert result is None

    async def test_invalidate_by_pattern(self, cache: ResponseCache) -> None:
        await cache.set("user:alice", {"name": "Alice"}, ttl=60.0)
        await cache.set("user:bob", {"name": "Bob"}, ttl=60.0)
        await cache.set("admin:config", {"key": "val"}, ttl=60.0)
        count = await cache.invalidate("user:")
        assert count == 2
        assert await cache.get("user:alice") is None
        assert await cache.get("user:bob") is None
        assert await cache.get("admin:config") is not None

    async def test_invalidate_no_match(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "hello"}, ttl=60.0)
        count = await cache.invalidate("nonexistent")
        assert count == 0
        assert await cache.get("key1") is not None

    async def test_clear(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "hello"}, ttl=60.0)
        await cache.set("key2", {"data": "world"}, ttl=60.0)
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    async def test_get_stats(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "hello"}, ttl=60.0)
        stats = await cache.get_stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert "default_ttl" in stats
        assert "hit_count" in stats
        assert "miss_count" in stats

    async def test_lru_eviction(self, cache: ResponseCache) -> None:
        small_cache = ResponseCache(max_size=3, default_ttl=60.0)
        await small_cache.set("a", {"v": 1}, ttl=60.0)
        await small_cache.set("b", {"v": 2}, ttl=60.0)
        await small_cache.set("c", {"v": 3}, ttl=60.0)
        await small_cache.set("d", {"v": 4}, ttl=60.0)
        assert await small_cache.get("a") is None
        assert await small_cache.get("d") is not None

    async def test_lru_eviction_skips_recently_used(self, cache: ResponseCache) -> None:
        small_cache = ResponseCache(max_size=2, default_ttl=60.0)
        await small_cache.set("a", {"v": 1}, ttl=60.0)
        await small_cache.set("b", {"v": 2}, ttl=60.0)
        await small_cache.get("a")
        await small_cache.set("c", {"v": 3}, ttl=60.0)
        assert await small_cache.get("a") is not None
        assert await small_cache.get("b") is None

    async def test_set_with_custom_ttl(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "hello"}, ttl=10.0)
        entry = await cache.get("key1")
        assert entry is not None
        assert (entry.expires_at - entry.created_at).total_seconds() == pytest.approx(10.0, abs=1.0)

    async def test_set_with_status_and_headers(self, cache: ResponseCache) -> None:
        await cache.set(
            "key1",
            {"data": "hello"},
            ttl=60.0,
            status_code=201,
            headers={"x-custom": "val"},
        )
        entry = await cache.get("key1")
        assert entry is not None
        assert entry.status_code == 201
        assert entry.headers == {"x-custom": "val"}

    async def test_set_updates_existing_key(self, cache: ResponseCache) -> None:
        await cache.set("key1", {"data": "first"}, ttl=60.0)
        await cache.set("key1", {"data": "second"}, ttl=60.0)
        entry = await cache.get("key1")
        assert entry is not None
        assert entry.response_body == {"data": "second"}
