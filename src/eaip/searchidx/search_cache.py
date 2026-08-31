"""SearchCache — get-or-compute, invalidate, warm, stats."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from eaip.searchidx.exceptions import CacheNotFoundError
from eaip.searchidx.models import SearchCacheConfig


class SearchCache:
    """In-memory cache with TTL support for search results."""

    def __init__(self, config: SearchCacheConfig | None = None) -> None:
        """Initialize the search cache with optional config."""
        self._config = config or SearchCacheConfig()
        self._store: dict[str, tuple[Any, float]] = {}
        self._hits: int = 0
        self._misses: int = 0

    @property
    def config(self) -> SearchCacheConfig:
        """Return the cache configuration."""
        return self._config

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Awaitable[Any]],
        ttl: int | None = None,
    ) -> Any:
        """Return cached value or compute and cache it."""
        if not self._config.enable_cache:
            return await compute_fn()

        now = time.monotonic()
        if key in self._store:
            value, expiry = self._store[key]
            if now < expiry:
                self._hits += 1
                return value
            del self._store[key]

        self._misses += 1
        value = await compute_fn()
        effective_ttl = ttl if ttl is not None else self._config.default_ttl_seconds
        self._store[key] = (value, now + effective_ttl)

        if len(self._store) > self._config.max_cache_size:
            oldest_key = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest_key]

        return value

    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching a key pattern."""
        removed = 0
        keys = list(self._store.keys())
        for key in keys:
            if pattern in key:
                del self._store[key]
                removed += 1
        return removed

    async def warm(self, keys: list[str]) -> int:
        """Pre-populate cache entries (stub)."""
        warmed = 0
        for key in keys:
            if key not in self._store:
                self._store[key] = (None, time.monotonic() + self._config.default_ttl_seconds)
                warmed += 1
        return warmed

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    async def get_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._store),
            "max_size": self._config.max_cache_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "enabled": self._config.enable_cache,
        }

    async def get(self, key: str) -> Any:
        """Get a value by key, raising if not found or expired."""
        if key not in self._store:
            raise CacheNotFoundError(
                f"Cache key {key!r} not found.",
                context={"key": key},
            )
        value, expiry = self._store[key]
        if time.monotonic() >= expiry:
            del self._store[key]
            raise CacheNotFoundError(
                f"Cache key {key!r} has expired.",
                context={"key": key},
            )
        self._hits += 1
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a cache value with optional TTL."""
        effective_ttl = ttl if ttl is not None else self._config.default_ttl_seconds
        self._store[key] = (value, time.monotonic() + effective_ttl)


__all__ = ["SearchCache"]
