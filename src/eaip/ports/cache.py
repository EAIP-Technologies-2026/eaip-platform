"""Cache provider port — abstract dependency for the response cache.

The :class:`CacheProvider` protocol lets callers swap the in-memory
``ResponseCache`` for a Redis-backed or other distributed implementation
without changing service code.

Usage::

    from eaip.ports.cache import CacheProvider


    class RedisCache:
        async def get(self, key: str) -> CachedResponse | None: ...
        async def set(self, key: str, value: CachedResponse, ttl: float) -> None: ...
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CacheProvider(Protocol):
    """Pluggable cache backend contract.

    Implementations must be thread-safe and async-friendly.
    """

    async def get(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: The cache key.

        Returns:
            The cached value, or ``None`` if missing or expired.
        """
        ...

    async def set(self, key: str, value: Any, ttl: float) -> None:
        """Store a value with a TTL.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time-to-live in seconds.
        """
        ...

    async def invalidate(self, pattern: str) -> int:
        """Remove all entries matching *pattern*.

        Args:
            pattern: A substring to match against cache keys.

        Returns:
            The number of invalidated entries.
        """
        ...

    async def invalidate_one(self, key: str) -> bool:
        """Remove a single key.

        Args:
            key: The exact cache key to remove.

        Returns:
            ``True`` if the key existed.
        """
        ...

    async def clear(self) -> None:
        """Remove every entry from the cache."""
        ...

    async def get_stats(self) -> dict[str, Any]:
        """Return cache statistics (size, hits, misses, evictions, …)."""
        ...


__all__ = ["CacheProvider"]
