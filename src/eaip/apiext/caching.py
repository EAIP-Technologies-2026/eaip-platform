"""Response cache — in-memory cache with TTL and LRU eviction."""

from __future__ import annotations

import time
from typing import Any

from eaip.apiext.events import CacheHit, CacheInvalidated, CacheMiss
from eaip.apiext.models import CachedResponse
from eaip.events.bus import EventBus
from eaip.infrastructure.cache import InMemoryCacheProvider
from eaip.logging.context import get_logger
from eaip.ports.cache import CacheProvider
from eaip.shared.time import utc_now


class ResponseCache:
    """Response cache backed by a pluggable :class:`CacheProvider`.

    Defaults to :class:`InMemoryCacheProvider`; swap for a Redis-backed
    adapter via DI without changing this class.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 300.0,
        event_bus: EventBus | None = None,
        cache_provider: CacheProvider | None = None,
    ) -> None:
        """Initialize the cache.

        Args:
            max_size: Maximum number of entries before LRU eviction
                (used only when *cache_provider* is ``None``).
            default_ttl: Default TTL in seconds for cached responses.
            event_bus: Optional event bus for publishing cache events.
            cache_provider: Optional pluggable cache backend.
                Defaults to :class:`InMemoryCacheProvider`.
        """
        self._default_ttl = default_ttl
        self._cache = cache_provider or InMemoryCacheProvider(max_size=max_size, default_ttl=default_ttl)
        self._log = get_logger("eaip.apiext.caching")
        self._event_bus = event_bus

    async def get(self, cache_key: str) -> CachedResponse | None:
        """Retrieve a cached response by key.

        Args:
            cache_key: The cache key.

        Returns:
            The cached response if found and not expired, or ``None``.
        """
        entry = await self._cache.get(cache_key)
        if entry is None:
            await self._publish_cache_event(CacheMiss(cache_key=cache_key))
            return None

        if isinstance(entry, CachedResponse):
            if utc_now() >= entry.expires_at:
                await self._cache.invalidate_one(cache_key)
                await self._publish_cache_event(CacheMiss(cache_key=cache_key))
                return None

            updated = CachedResponse(
                id=entry.id,
                cache_key=entry.cache_key,
                response_body=entry.response_body,
                status_code=entry.status_code,
                headers=entry.headers,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
                hit_count=entry.hit_count + 1,
            )
            await self._cache.set(cache_key, updated, ttl=(entry.expires_at - utc_now()).total_seconds())
            await self._publish_cache_event(CacheHit(cache_key=cache_key, hit_count=updated.hit_count))
            return updated
        return entry

    async def set(
        self,
        cache_key: str,
        response: dict[str, Any],
        ttl: float | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> CachedResponse:
        """Store a response in the cache.

        Args:
            cache_key: The cache key.
            response: The response body to cache.
            ttl: TTL in seconds (defaults to ``self._default_ttl``).
            status_code: The HTTP status code.
            headers: The response headers.

        Returns:
            The created cache entry.
        """
        effective_ttl = ttl if ttl is not None else self._default_ttl
        now = utc_now()
        try:
            from datetime import timedelta

            expires_at = now + timedelta(seconds=effective_ttl)
        except Exception:
            expires_at = now

        entry_id = f"cache_{cache_key}_{int(time.time())}"
        entry = CachedResponse(
            id=entry_id,
            cache_key=cache_key,
            response_body=response,
            status_code=status_code,
            headers=headers or {},
            created_at=now,
            expires_at=expires_at,
        )
        await self._cache.set(cache_key, entry, ttl=effective_ttl)
        return entry

    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching a key pattern.

        Args:
            pattern: A substring to match against cache keys.

        Returns:
            The number of invalidated entries.
        """
        count = await self._cache.invalidate(pattern)
        if count > 0 and self._event_bus is not None:
            await self._event_bus.publish(
                CacheInvalidated(cache_key=pattern, pattern=pattern)
            )
        return count

    async def clear(self) -> None:
        """Clear all cache entries."""
        await self._cache.clear()
        self._log.info("apiext.cache.cleared")

    async def get_stats(self) -> dict[str, Any]:
        """Return cache statistics.

        Returns:
            A dict with size, max_size, hit/miss counts, and hit distribution.
        """
        stats = await self._cache.get_stats()
        stats["default_ttl"] = self._default_ttl
        stats.setdefault("hit_counts", {})
        return stats

    async def _publish_cache_event(self, event: Any) -> None:
        """Publish a cache event if an event bus is configured."""
        if self._event_bus is not None:
            await self._event_bus.publish(event)
