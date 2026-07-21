"""Abstract cache provider and built-in implementations."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime, timedelta

from eaip.cache.models import CacheEntry, CacheStats
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class CacheProvider(ABC):
    """Abstract base class for all cache backends."""

    @abstractmethod
    async def get(self, key: str) -> bytes | None:
        """Retrieve a value by key. Returns None on miss."""

    @abstractmethod
    async def set(
        self,
        key: str,
        value: bytes,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store a value with optional TTL."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if it existed."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check whether a key exists in the cache."""

    @abstractmethod
    async def clear(self) -> int:
        """Remove all entries. Returns the number removed."""

    @abstractmethod
    async def get_stats(self) -> CacheStats:
        """Return a snapshot of cache statistics."""

    @abstractmethod
    async def close(self) -> None:
        """Release any resources held by the provider."""


class InMemoryCache(CacheProvider):
    """Thread-safe, dict-based cache with TTL expiry and LRU eviction."""

    def __init__(
        self,
        max_entries: int = 10000,
        max_size_bytes: int = 0,
        namespace: str = "default",
    ) -> None:
        """Initialize the cache with capacity limits."""
        self._max_entries = max_entries
        self._max_size_bytes = max_size_bytes
        self._namespace = namespace
        self._lock = threading.Lock()
        self._data: OrderedDict[str, CacheEntry] = OrderedDict()
        self._total_hits = 0
        self._total_misses = 0
        self._total_evictions = 0
        self._current_size_bytes = 0
        self._log = get_logger(f"eaip.cache.in_memory.{namespace}")

    async def get(self, key: str) -> bytes | None:
        """Retrieve a value by key. Returns None on miss or expiry."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self._total_misses += 1
                return None
            if entry.expires_at is not None and utc_now() >= entry.expires_at:
                self._data.pop(key, None)
                self._current_size_bytes -= entry.size_bytes
                self._total_evictions += 1
                self._total_misses += 1
                return None
            self._data.move_to_end(key)
            entry = entry.model_copy(update={"hits": entry.hits + 1})
            self._data[key] = entry
            self._total_hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: bytes,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store a value with optional TTL."""
        size_bytes = len(value)
        now = utc_now()
        expires_at: datetime | None = None
        if ttl_seconds is not None:
            expires_at = now + timedelta(seconds=ttl_seconds)

        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            created_at=now,
            expires_at=expires_at,
            size_bytes=size_bytes,
        )

        with self._lock:
            old_entry = self._data.get(key)
            if old_entry is not None:
                self._current_size_bytes -= old_entry.size_bytes
                del self._data[key]

            self._evict_if_needed(size_bytes)
            self._data[key] = entry
            self._data.move_to_end(key)
            self._current_size_bytes += size_bytes

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if it existed."""
        with self._lock:
            entry = self._data.pop(key, None)
            if entry is None:
                return False
            self._current_size_bytes -= entry.size_bytes
            return True

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            if entry.expires_at is not None and utc_now() >= entry.expires_at:
                self._data.pop(key, None)
                self._current_size_bytes -= entry.size_bytes
                self._total_evictions += 1
                return False
            return True

    async def clear(self) -> int:
        """Remove all entries. Returns the number removed."""
        with self._lock:
            count = len(self._data)
            self._data.clear()
            self._current_size_bytes = 0
            self._total_hits = 0
            self._total_misses = 0
            self._total_evictions = 0
            return count

    async def get_stats(self) -> CacheStats:
        """Return a snapshot of cache statistics."""
        with self._lock:
            total = self._total_hits + self._total_misses
            hit_ratio = self._total_hits / total if total > 0 else 0.0
            return CacheStats(
                total_entries=len(self._data),
                total_hits=self._total_hits,
                total_misses=self._total_misses,
                total_evictions=self._total_evictions,
                hit_ratio=round(hit_ratio, 4),
                size_bytes=self._current_size_bytes,
            )

    async def close(self) -> None:
        """Release resources and clear all data."""
        self._data.clear()
        self._current_size_bytes = 0

    def _evict_if_needed(self, incoming_size: int) -> None:
        """Evict entries if capacity limits are exceeded."""
        if self._max_entries > 0:
            while len(self._data) >= self._max_entries:
                _key, entry = self._data.popitem(last=False)
                self._current_size_bytes -= entry.size_bytes
                self._total_evictions += 1
                self._log.info("cache.evict.lru", key=_key, namespace=self._namespace)
        if self._max_size_bytes > 0:
            while self._current_size_bytes + incoming_size > self._max_size_bytes and self._data:
                _key, entry = self._data.popitem(last=False)
                self._current_size_bytes -= entry.size_bytes
                self._total_evictions += 1
                self._log.info("cache.evict.size", key=_key, namespace=self._namespace)

    @property
    def namespace(self) -> str:
        """Return the cache namespace."""
        return self._namespace


class NullCache(CacheProvider):
    """No-op cache implementation that never stores anything."""

    def __init__(self, namespace: str = "null") -> None:
        """Initialize with a namespace."""
        self._namespace = namespace

    async def get(self, key: str) -> bytes | None:  # noqa: ARG002
        """Always returns None."""
        return None

    async def set(
        self,
        key: str,
        value: bytes,
        ttl_seconds: int | None = None,
    ) -> None:
        """No-op."""

    async def delete(self, key: str) -> bool:  # noqa: ARG002
        """Always returns False."""
        return False

    async def exists(self, key: str) -> bool:  # noqa: ARG002
        """Always returns False."""
        return False

    async def clear(self) -> int:
        """Always returns 0."""
        return 0

    async def get_stats(self) -> CacheStats:
        """Return empty stats."""
        return CacheStats()

    async def close(self) -> None:
        """No-op."""
