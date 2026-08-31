"""Integration layer — SearchIndexRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger
from eaip.searchidx.cache_warmer import CacheWarmer
from eaip.searchidx.health import SearchIndexHealthCheck
from eaip.searchidx.index_manager import IndexManager
from eaip.searchidx.search_cache import SearchCache

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SearchIndexRuntimeModule:
    """RuntimeModule that bootstraps the Search Index subsystem during kernel start."""

    name: str = "searchidx"

    def __init__(
        self,
        index_manager: IndexManager | None = None,
        search_cache: SearchCache | None = None,
        cache_warmer: CacheWarmer | None = None,
    ) -> None:
        """Initialize with optional managers."""
        self._index_manager = index_manager or IndexManager()
        self._search_cache = search_cache or SearchCache()
        self._cache_warmer = cache_warmer or CacheWarmer(search_cache=self._search_cache)
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.searchidx.integration")

    @property
    def index_manager(self) -> IndexManager:
        """Return the index manager."""
        return self._index_manager

    @property
    def search_cache(self) -> SearchCache:
        """Return the search cache."""
        return self._search_cache

    @property
    def cache_warmer(self) -> CacheWarmer:
        """Return the cache warmer."""
        return self._cache_warmer

    @property
    def startup_duration(self) -> float:
        """Return the startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the module and register health check."""
        t0 = time.monotonic()
        self._log.info("searchidx.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "searchidx.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the module."""
        self._log.info("searchidx.integration.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        """Create a health check instance."""
        indices = self._index_manager.list_indices()
        ready = sum(1 for i in indices if i.status == "ready")
        return SearchIndexHealthCheck(
            index_count=len(indices),
            ready_indices=ready,
            cache_available=True,
        )


__all__ = ["SearchIndexRuntimeModule"]
