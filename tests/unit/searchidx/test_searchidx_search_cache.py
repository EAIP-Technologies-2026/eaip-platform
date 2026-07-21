from __future__ import annotations

import pytest

from eaip.searchidx.exceptions import CacheNotFoundError
from eaip.searchidx.models import SearchCacheConfig
from eaip.searchidx.search_cache import SearchCache


class _Fixture:
    def __init__(self) -> None:
        self.cache = SearchCache()


@pytest.fixture
def fixture() -> _Fixture:
    return _Fixture()


class TestSearchCache:
    @pytest.mark.asyncio
    async def test_get_or_compute_caches(self, fixture: _Fixture) -> None:
        call_count = 0

        async def compute() -> str:
            nonlocal call_count
            call_count += 1
            return "result"

        r1 = await fixture.cache.get_or_compute("k1", compute)
        r2 = await fixture.cache.get_or_compute("k1", compute)
        assert r1 == "result"
        assert r2 == "result"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_get_or_compute_expired(self, fixture: _Fixture) -> None:
        call_count = 0

        async def compute() -> str:
            nonlocal call_count
            call_count += 1
            return "data"

        await fixture.cache.get_or_compute("k1", compute, ttl=-1)
        await fixture.cache.get_or_compute("k1", compute, ttl=60)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_or_compute_cache_disabled(self, fixture: _Fixture) -> None:
        cfg = SearchCacheConfig(enable_cache=False)
        cache = SearchCache(config=cfg)
        call_count = 0

        async def compute() -> str:
            nonlocal call_count
            call_count += 1
            return "val"

        await cache.get_or_compute("k1", compute)
        await cache.get_or_compute("k1", compute)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate(self, fixture: _Fixture) -> None:
        async def compute() -> str:
            return "val"

        await fixture.cache.get_or_compute("prefix:1", compute)
        await fixture.cache.get_or_compute("prefix:2", compute)
        await fixture.cache.get_or_compute("other:1", compute)
        removed = await fixture.cache.invalidate("prefix:")
        assert removed == 2

    @pytest.mark.asyncio
    async def test_invalidate_no_match(self, fixture: _Fixture) -> None:
        removed = await fixture.cache.invalidate("nonexistent")
        assert removed == 0

    @pytest.mark.asyncio
    async def test_warm(self, fixture: _Fixture) -> None:
        warmed = await fixture.cache.warm(["k1", "k2"])
        assert warmed == 2

    @pytest.mark.asyncio
    async def test_warm_existing(self, fixture: _Fixture) -> None:
        async def compute() -> str:
            return "val"

        await fixture.cache.get_or_compute("k1", compute)
        warmed = await fixture.cache.warm(["k1"])
        assert warmed == 0

    @pytest.mark.asyncio
    async def test_clear(self, fixture: _Fixture) -> None:
        async def compute() -> str:
            return "val"

        await fixture.cache.get_or_compute("k1", compute)
        await fixture.cache.clear()
        stats = await fixture.cache.get_stats()
        assert stats["size"] == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, fixture: _Fixture) -> None:
        async def compute() -> str:
            return "val"

        await fixture.cache.get_or_compute("k1", compute)
        stats = await fixture.cache.get_stats()
        assert stats["size"] >= 1
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_hit_rate(self, fixture: _Fixture) -> None:
        async def compute() -> str:
            return "val"

        await fixture.cache.get_or_compute("k1", compute)
        await fixture.cache.get_or_compute("k1", compute)
        stats = await fixture.cache.get_stats()
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get(self, fixture: _Fixture) -> None:
        async def compute() -> str:
            return "val"

        await fixture.cache.get_or_compute("k1", compute)
        val = await fixture.cache.get("k1")
        assert val == "val"

    @pytest.mark.asyncio
    async def test_get_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(CacheNotFoundError):
            await fixture.cache.get("nonexistent")

    @pytest.mark.asyncio
    async def test_get_expired(self, fixture: _Fixture) -> None:
        async def compute() -> str:
            return "val"

        await fixture.cache.get_or_compute("k1", compute, ttl=-1)
        with pytest.raises(CacheNotFoundError):
            await fixture.cache.get("k1")

    @pytest.mark.asyncio
    async def test_set(self, fixture: _Fixture) -> None:
        await fixture.cache.set("k1", "value")
        val = await fixture.cache.get("k1")
        assert val == "value"

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, fixture: _Fixture) -> None:
        await fixture.cache.set("k1", "value", ttl=60)
        val = await fixture.cache.get("k1")
        assert val == "value"

    @pytest.mark.asyncio
    async def test_max_cache_size_eviction(self, fixture: _Fixture) -> None:
        cfg = SearchCacheConfig(max_cache_size=2)
        cache = SearchCache(config=cfg)

        async def compute(v: str):
            async def _inner() -> str:
                return v

            return _inner

        await cache.get_or_compute("k1", await compute("a"))
        await cache.get_or_compute("k2", await compute("b"))
        await cache.get_or_compute("k3", await compute("c"))
        stats = await cache.get_stats()
        assert stats["size"] <= 2

    def test_property(self, fixture: _Fixture) -> None:
        assert isinstance(fixture.cache.config, SearchCacheConfig)
