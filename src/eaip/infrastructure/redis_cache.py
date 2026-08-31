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

from eaip.logging.context import get_logger
from eaip.ports.cache import CacheProvider

log = get_logger("eaip.infrastructure.redis_cache")


class RedisCacheProvider(CacheProvider):
    """Production Redis cache implementing :class:`CacheProvider`.

    Uses redis.asyncio for non-blocking Redis operations.

    Redis is treated as an **optional, non-authoritative** cache layer.  When
    Redis is unavailable (unreachable or the ``redis`` package is not
    installed) every operation degrades to a safe no-op:

    - ``get`` returns ``None`` (a cache miss), never raises.
    - ``set`` / ``invalidate`` / ``clear`` log a warning and continue.

    This preserves correctness of the authoritative stores (PostgreSQL, event
    store, audit) while keeping latency out of the hot path.  A cache miss is
    an acceptable degradation; silent data loss is not possible because the
    cache is never the source of truth.
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
        self._degraded: bool = False

    @staticmethod
    def tenant_key(tenant_id: str, namespace: str, key: str) -> str:
        """Build a tenant-scoped cache key that cannot collide across tenants.

        Example: ``tenant:acme:knowledge:doc-123``.
        """
        return f"tenant:{tenant_id}:{namespace}:{key}"

    async def _ensure_redis(self) -> Any:
        if self._redis is None:
            try:
                import redis.asyncio as aioredis  # type: ignore[import-not-found]

                self._redis = aioredis.from_url(
                    self._redis_url,
                    max_connections=self._pool_max_size,
                    socket_timeout=self._socket_timeout,
                    socket_connect_timeout=self._socket_connect_timeout,
                    decode_responses=True,
                )
            except (ImportError, ModuleNotFoundError, AttributeError):
                self._degraded = True
                log.warning(
                    "redis.unavailable", error="redis package not installed", url=self._redis_url
                )
                self._redis = None
        return self._redis

    async def _available(self) -> Any:
        client = await self._ensure_redis()
        if client is None:
            return None
        try:
            if await client.ping():
                self._degraded = False
                return client
        except Exception:
            pass
        if not self._degraded:
            self._degraded = True
            log.warning("redis.degraded", url=self._redis_url)
        return None

    async def get(self, key: str) -> Any | None:
        client = await self._available()
        if client is None:
            self._miss_count += 1
            return None
        try:
            value = await client.get(key)
            if value is None:
                self._miss_count += 1
                return None
            self._hit_count += 1
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception:
            self._miss_count += 1
            log.warning("redis.get.failed", key=key)
            return None

    async def set(self, key: str, value: Any, ttl: float) -> None:
        client = await self._available()
        if client is None:
            log.warning("redis.set.skipped", key=key, reason="unavailable")
            return
        try:
            serialized = json.dumps(value, default=str)
            await client.setex(key, int(ttl), serialized)
        except Exception:
            log.warning("redis.set.failed", key=key)

    async def invalidate(self, pattern: str) -> int:
        client = await self._available()
        if client is None:
            return 0
        try:
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception:
            log.warning("redis.invalidate.failed", pattern=pattern)
            return 0

    async def invalidate_one(self, key: str) -> bool:
        client = await self._available()
        if client is None:
            return False
        try:
            result = await client.delete(key)
            return result > 0
        except Exception:
            log.warning("redis.invalidate_one.failed", key=key)
            return False

    async def clear(self) -> None:
        client = await self._available()
        if client is None:
            return
        try:
            await client.flushdb()
        except Exception:
            log.warning("redis.clear.failed")

    async def get_stats(self) -> dict[str, Any]:
        client = await self._available()
        total = self._hit_count + self._miss_count
        hit_rate = round(self._hit_count / total * 100, 2) if total > 0 else 0.0
        stats: dict[str, Any] = {
            "type": "redis",
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_pct": hit_rate,
            "degraded": self._degraded,
        }
        if client is None:
            return stats
        try:
            info = await client.info("stats")
            stats["redis_keyspace_hits"] = info.get("keyspace_hits", 0)
            stats["redis_keyspace_misses"] = info.get("keyspace_misses", 0)
        except Exception:
            stats["redis_keyspace_hits"] = 0
            stats["redis_keyspace_misses"] = 0
        return stats

    async def close(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.close()
            except Exception:
                pass
            self._redis = None

    async def ping(self) -> bool:
        """Health check — returns True if Redis is reachable."""
        try:
            client = await self._available()
            return client is not None
        except Exception:
            return False


__all__ = ["RedisCacheProvider"]
