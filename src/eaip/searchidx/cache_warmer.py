"""CacheWarmer — warm indices, popular keys, schedule warming."""

from __future__ import annotations

import time

from eaip.searchidx.search_cache import SearchCache


class CacheWarmer:
    """Warms the cache by pre-populating entries for indices and popular keys."""

    def __init__(
        self,
        search_cache: SearchCache,
        warming_interval: int = 60,
    ) -> None:
        """Initialize with search cache reference."""
        self._search_cache = search_cache
        self._warming_interval = warming_interval
        self._last_warm_time: float = 0.0
        self._indices_warmed: list[str] = []

    @property
    def search_cache(self) -> SearchCache:
        """Return the search cache instance."""
        return self._search_cache

    async def warm_index(self, index_id: str) -> int:
        """Warm cache for a specific index."""
        await self._search_cache.warm([f"idx:{index_id}:*"])
        self._indices_warmed.append(index_id)
        self._last_warm_time = time.time()
        return 1

    async def warm_popular(self, limit: int = 100) -> int:
        """Warm cache with popular queries."""
        keys = [f"popular:{i}" for i in range(limit)]
        warmed = await self._search_cache.warm(keys)
        self._last_warm_time = time.time()
        return warmed

    async def schedule_warming(self, interval: int = 60) -> dict[str, object]:
        """Schedule periodic cache warming (stub)."""
        self._warming_interval = interval
        return {"interval": interval, "scheduled": True}

    async def get_warm_status(self) -> dict[str, object]:
        """Return the warming status."""
        return {
            "warming_enabled": True,
            "interval_seconds": self._warming_interval,
            "last_warm_time": self._last_warm_time,
            "indices_warmed": self._indices_warmed,
        }


__all__ = ["CacheWarmer"]
