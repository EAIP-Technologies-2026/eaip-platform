"""Multi-level cache manager implementing the cache-aside pattern."""

from __future__ import annotations

from typing import Any

from eaip.cache.models import CacheConfig, CacheStats
from eaip.cache.provider import CacheProvider, InMemoryCache, NullCache
from eaip.logging.context import get_logger


class CacheManager:
    """Multi-level cache with cache-aside pattern.

    L1 is always an in-memory cache. An optional L2 backing cache
    (e.g. Redis) provides a second tier. Stats are aggregated across
    all configured levels.
    """

    def __init__(
        self,
        config: CacheConfig | None = None,
        l2_provider: CacheProvider | None = None,
    ) -> None:
        """Initialize the manager with config and optional L2 provider."""
        self._config = config or CacheConfig()
        self._l1 = InMemoryCache(
            max_entries=self._config.max_entries,
            max_size_bytes=self._config.max_size_bytes,
            namespace=self._config.namespace,
        )
        self._l2 = l2_provider or NullCache(namespace=f"{self._config.namespace}_l2")
        self._log = get_logger(f"eaip.cache.manager.{self._config.namespace}")

    @property
    def config(self) -> CacheConfig:
        """Return the cache configuration."""
        return self._config

    async def get(self, key: str) -> bytes | None:
        """Retrieve a value by key, checking L1 then L2."""
        value = await self._l1.get(key)
        if value is not None:
            self._log.debug("cache.l1_hit", key=key)
            return value

        value = await self._l2.get(key)
        if value is not None:
            self._log.debug("cache.l2_hit", key=key)
            ttl = self._config.default_ttl_seconds
            await self._l1.set(key, value, ttl_seconds=ttl)
            return value

        self._log.debug("cache.miss", key=key)
        return None

    async def get_or_compute(
        self,
        key: str,
        factory: Any,
        ttl_seconds: int | None = None,
    ) -> bytes:
        """Return cached value or compute and cache it."""
        cached = await self.get(key)
        if cached is not None:
            return cached
        result = await factory() if callable(factory) else factory
        value = bytes(result) if not isinstance(result, bytes) else result
        await self.set(key, value, ttl_seconds=ttl_seconds)
        return value

    async def set(
        self,
        key: str,
        value: bytes,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store a value in both L1 and L2."""
        effective_ttl = ttl_seconds if ttl_seconds is not None else self._config.default_ttl_seconds
        await self._l1.set(key, value, ttl_seconds=effective_ttl)
        await self._l2.set(key, value, ttl_seconds=effective_ttl)

    async def delete(self, key: str) -> bool:
        """Delete a key from both L1 and L2."""
        d1 = await self._l1.delete(key)
        d2 = await self._l2.delete(key)
        return d1 or d2

    async def exists(self, key: str) -> bool:
        """Check if a key exists in L1 or L2."""
        if await self._l1.exists(key):
            return True
        return await self._l2.exists(key)

    async def clear(self) -> int:
        """Clear all entries from L1 and L2."""
        c1 = await self._l1.clear()
        c2 = await self._l2.clear()
        return c1 + c2

    async def get_stats(self) -> CacheStats:
        """Return aggregated cache statistics."""
        s1 = await self._l1.get_stats()
        s2 = await self._l2.get_stats()
        total = s1.total_hits + s2.total_hits + s1.total_misses + s2.total_misses
        total_hits = s1.total_hits + s2.total_hits
        hit_ratio = total_hits / total if total > 0 else 0.0
        return CacheStats(
            total_entries=s1.total_entries + s2.total_entries,
            total_hits=total_hits,
            total_misses=s1.total_misses + s2.total_misses,
            total_evictions=s1.total_evictions + s2.total_evictions,
            hit_ratio=round(hit_ratio, 4),
            size_bytes=s1.size_bytes + s2.size_bytes,
        )

    async def close(self) -> None:
        """Close both cache providers."""
        await self._l1.close()
        await self._l2.close()
