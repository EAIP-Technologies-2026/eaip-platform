from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.searchidx.cache_warmer import CacheWarmer
from eaip.searchidx.index_manager import IndexManager
from eaip.searchidx.integration import SearchIndexRuntimeModule
from eaip.searchidx.search_cache import SearchCache


class TestSearchidxIntegration:
    def test_default_initialization(self) -> None:
        mod = SearchIndexRuntimeModule()
        assert mod.name == "searchidx"
        assert isinstance(mod.index_manager, IndexManager)
        assert isinstance(mod.search_cache, SearchCache)
        assert isinstance(mod.cache_warmer, CacheWarmer)

    def test_custom_initialization(self) -> None:
        im = IndexManager()
        sc = SearchCache()
        cw = CacheWarmer(search_cache=sc)
        mod = SearchIndexRuntimeModule(
            index_manager=im,
            search_cache=sc,
            cache_warmer=cw,
        )
        assert mod.index_manager is im
        assert mod.search_cache is sc
        assert mod.cache_warmer is cw

    def test_startup_duration_default(self) -> None:
        mod = SearchIndexRuntimeModule()
        assert mod.startup_duration == 0.0

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = SearchIndexRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        assert mod.startup_duration > 0.0
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = SearchIndexRuntimeModule()
        await mod.stop()

    @pytest.mark.asyncio
    async def test_start_without_kernel(self) -> None:
        mod = SearchIndexRuntimeModule()
        await mod.start()
        assert mod.startup_duration > 0.0

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = SearchIndexRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert registered_check.name == "searchidx"
