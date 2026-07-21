from __future__ import annotations

import pytest

from eaip.searchidx.cache_warmer import CacheWarmer
from eaip.searchidx.search_cache import SearchCache


class _Fixture:
    def __init__(self) -> None:
        self.cache = SearchCache()
        self.warmer = CacheWarmer(search_cache=self.cache)


@pytest.fixture
def fixture() -> _Fixture:
    return _Fixture()


class TestCacheWarmer:
    @pytest.mark.asyncio
    async def test_warm_index(self, fixture: _Fixture) -> None:
        warmed = await fixture.warmer.warm_index("idx1")
        assert warmed >= 0

    @pytest.mark.asyncio
    async def test_warm_popular(self, fixture: _Fixture) -> None:
        warmed = await fixture.warmer.warm_popular(limit=10)
        assert warmed == 10

    @pytest.mark.asyncio
    async def test_warm_popular_default(self, fixture: _Fixture) -> None:
        warmed = await fixture.warmer.warm_popular()
        assert warmed == 100

    @pytest.mark.asyncio
    async def test_schedule_warming(self, fixture: _Fixture) -> None:
        result = await fixture.warmer.schedule_warming(interval=120)
        assert result["interval"] == 120
        assert result["scheduled"] is True

    @pytest.mark.asyncio
    async def test_get_warm_status_default(self, fixture: _Fixture) -> None:
        status = await fixture.warmer.get_warm_status()
        assert status["warming_enabled"] is True
        assert status["interval_seconds"] == 60
        assert status["last_warm_time"] == 0.0
        assert status["indices_warmed"] == []

    @pytest.mark.asyncio
    async def test_get_warm_status_after_warming(self, fixture: _Fixture) -> None:
        await fixture.warmer.warm_index("idx1")
        await fixture.warmer.warm_popular(5)
        status = await fixture.warmer.get_warm_status()
        assert "idx1" in status["indices_warmed"]
        assert status["last_warm_time"] > 0.0

    @pytest.mark.asyncio
    async def test_warm_index_multiple(self, fixture: _Fixture) -> None:
        await fixture.warmer.warm_index("idx1")
        await fixture.warmer.warm_index("idx2")
        status = await fixture.warmer.get_warm_status()
        assert len(status["indices_warmed"]) == 2

    def test_property(self, fixture: _Fixture) -> None:
        assert fixture.warmer.search_cache is fixture.cache
