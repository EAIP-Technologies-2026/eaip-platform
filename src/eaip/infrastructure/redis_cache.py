"""Redis-backed :class:`CacheProvider` implementation.

Provides a production-quality distributed cache behind the existing
:class:`CacheProvider` port.

Usage::

    from eaip.infrastructure.redis_cache import RedisCacheProvider

    cache = RedisCacheProvider(redis_url="redis://localhost:6379/0")
    await cache.set("key", value, ttl=300)
    value = await cache.get("key")
"""

from __future__ import annotations

import json
from typing import Any

from eaip.ports.cache import CacheProvider


class RedisCacheProvider(CacheProvider):
    """Production Redis cache implementing :class:`CacheProvider`.

    Uses redis.asyncio for non-blocking Redis operations.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        pool_min_size: int = 2,
        pool_max_size: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
    ) -> None:
        self._redis_url = redis_url
        self._pool_min_size = pool_min_size
        self._pool_max_size = pool_max_size
        self._socket_timeout = socket_timeout
        self._socket_connect_timeout = socket_connect_timeout
        self._redis: Any = None
        self._hit_count: int = 0
        self._miss_count: int = 0

    async def _ensure_redis(self) -> Any:
        if self._redis is None:
            import redis.asyncio as aioredis  # type: ignore[import-not-found]

            self._redis = aioredis.from_url(
                self._redis_url,
                max_connections=self._pool_max_size,
                socket_timeout=self._socket_timeout,
                socket_connect_timeout=self._socket_connect_timeout,
                decode_responses=True,
            )
        return self._redis

    async def get(self, key: str) -> Any | None:
        r = await self._ensure_redis()
        value = await r.get(key)
        if value is None:
            self._miss_count += 1
            return None
        self._hit_count += 1
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: float) -> None:
        r = await self._ensure_redis()
        serialized = json.dumps(value, default=str)
        await r.setex(key, int(ttl), serialized)

    async def invalidate(self, pattern: str) -> int:
        r = await self._ensure_redis()
        keys = await r.keys(pattern)
        if keys:
            return await r.delete(*keys)
        return 0

    async def invalidate_one(self, key: str) -> bool:
        r = await self._ensure_redis()
        result = await r.delete(key)
        return result > 0

    async def clear(self) -> None:
        r = await self._ensure_redis()
        await r.flushdb()

    async def get_stats(self) -> dict[str, Any]:
        r = await self._ensure_redis()
        info = await r.info("stats")
        total = self._hit_count + self._miss_count
        hit_rate = round(self._hit_count / total * 100, 2) if total > 0 else 0.0
        return {
            "type": "redis",
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_pct": hit_rate,
            "redis_keyspace_hits": info.get("keyspace_hits", 0),
            "redis_keyspace_misses": info.get("keyspace_misses", 0),
        }

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def ping(self) -> bool:
        """Health check — returns True if Redis is reachable."""
        try:
            r = await self._ensure_redis()
            return await r.ping()
        except Exception:
            return False


__all__ = ["RedisCacheProvider"]
