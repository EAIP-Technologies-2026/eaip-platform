"""Default :class:`CacheProvider` implementation — in-memory OrderedDict.

This is the built-in cache provider used when no external cache (e.g. Redis) is
configured.  Production deployments swap it for a Redis-backed adapter via the
DI container without changing consuming code.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from eaip.ports.cache import CacheProvider


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float = field(default=0.0)


class InMemoryCacheProvider(CacheProvider):
    """Bounded, TTL-aware in-memory cache with LRU eviction.

    Implements :class:`CacheProvider` using an ``OrderedDict`` for O(1)
    lookups and LRU-ordered iteration.
    """

    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._hit_count: int = 0
        self._miss_count: int = 0
        self._eviction_count: int = 0

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            self._miss_count += 1
            return None
        if self._is_expired(entry):
            del self._store[key]
            self._miss_count += 1
            return None
        self._store.move_to_end(key)
        self._hit_count += 1
        return entry.value

    async def set(self, key: str, value: Any, ttl: float) -> None:
        expires_at = time.monotonic() + ttl if ttl > 0 else 0.0
        self._store[key] = _CacheEntry(value=value, expires_at=expires_at)
        self._store.move_to_end(key)
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)
            self._eviction_count += 1

    async def invalidate(self, pattern: str) -> int:
        keys = [k for k in self._store if pattern in k]
        for k in keys:
            del self._store[k]
        return len(keys)

    async def invalidate_one(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def clear(self) -> None:
        self._store.clear()

    async def get_stats(self) -> dict[str, Any]:
        total = self._hit_count + self._miss_count
        hit_rate = round(self._hit_count / total * 100, 2) if total > 0 else 0.0
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_pct": hit_rate,
            "eviction_count": self._eviction_count,
        }

    async def cleanup_expired(self) -> int:
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if v.expires_at > 0 and now >= v.expires_at]
        for k in expired:
            del self._store[k]
        return len(expired)

    @staticmethod
    def _is_expired(entry: _CacheEntry) -> bool:
        return entry.expires_at > 0 and time.monotonic() >= entry.expires_at


__all__ = ["InMemoryCacheProvider"]
