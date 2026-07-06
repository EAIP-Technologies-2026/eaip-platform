"""InMemoryQueryCache — TTL-based cache implementing the QueryCache protocol.

The :class:`InMemoryQueryCache` provides a lightweight, asyncio-safe cache
that stores query results in memory with optional TTL expiration.  Expired
entries are lazily evicted on access and periodically cleaned up by a
background task.

Usage::

    from eaip.runtime.queries import QueryBus
    from eaip.runtime.cache import InMemoryQueryCache

    cache = InMemoryQueryCache(default_ttl=Duration.from_seconds(60))
    bus = QueryBus(cache=cache)
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any

from eaip.logging.context import get_logger
from eaip.shared.time import Duration, utc_now

if TYPE_CHECKING:
    from datetime import datetime

_DEFAULT_CLEANUP_INTERVAL = Duration.from_seconds(60)


class InMemoryQueryCache:
    """TTL-based in-memory cache implementing the :class:`QueryCache` protocol.

    Entries are stored in a dict with optional expiration timestamps.
    Stale entries are evicted lazily on get/delete/clear and periodically
    by a background cleanup task (started/stopped via :meth:`start` /
    :meth:`stop`).

    Parameters
    ----------
    default_ttl:
        Default TTL applied when ``set()`` is called without an explicit TTL.
        If ``None``, entries live forever unless explicitly deleted.
    cleanup_interval:
        How often the background cleanup runs (default: 60 seconds).
        Set to ``None`` to disable background cleanup entirely.
    """

    def __init__(
        self,
        default_ttl: Duration | None = None,
        cleanup_interval: Duration | None = _DEFAULT_CLEANUP_INTERVAL,
    ) -> None:
        """Initialize cache with optional default TTL and cleanup interval."""
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._store: dict[str, object] = {}
        self._expires: dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task[None] | None = None
        self._log = get_logger("eaip.runtime.cache")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background cleanup task (idempotent)."""
        if self._cleanup_task is not None:
            return
        if self._cleanup_interval is not None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._log.debug(
                "cache.cleanup.started",
                interval_seconds=self._cleanup_interval.seconds,
            )

    async def stop(self) -> None:
        """Stop the background cleanup task (idempotent)."""
        if self._cleanup_task is None:
            return
        self._cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._cleanup_task
        self._cleanup_task = None
        self._log.debug("cache.cleanup.stopped")

    # ------------------------------------------------------------------
    # QueryCache protocol
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Any | None:
        """Return the cached value for *key*, or ``None`` if absent or expired."""
        async with self._lock:
            self._evict_expired_now()
            return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: Duration | None = None) -> None:
        """Store *value* under *key* with an optional TTL.

        If *ttl* is ``None``, the ``default_ttl`` from construction is used.
        If that is also ``None``, the entry lives forever.
        """
        resolved_ttl = ttl if ttl is not None else self._default_ttl
        async with self._lock:
            self._store[key] = value
            if resolved_ttl is not None:
                self._expires[key] = utc_now() + resolved_ttl.to_timedelta()
            else:
                self._expires.pop(key, None)

    async def delete(self, key: str) -> bool:
        """Remove *key* from the cache.  Returns ``True`` if it existed."""
        async with self._lock:
            self._expires.pop(key, None)
            return self._store.pop(key, None) is not None

    async def clear(self) -> None:
        """Remove all entries from the cache."""
        async with self._lock:
            self._store.clear()
            self._expires.clear()

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Number of entries currently in the cache (approximate under concurrent access)."""
        return len(self._store)

    @property
    def keys(self) -> list[str]:
        """Return a snapshot of current cache keys."""
        return list(self._store.keys())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _evict_expired_now(self) -> None:
        """Remove expired entries (caller must hold ``_lock``)."""
        now = utc_now()
        stale = [k for k, exp in self._expires.items() if exp <= now]
        for k in stale:
            self._store.pop(k, None)
            self._expires.pop(k, None)
        if stale:
            self._log.debug("cache.evicted", count=len(stale))

    async def _cleanup_loop(self) -> None:
        """Periodic background cleanup of expired entries."""
        assert self._cleanup_interval is not None
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval.seconds)
                async with self._lock:
                    self._evict_expired_now()
            except asyncio.CancelledError:
                break
            except BaseException as exc:
                self._log.warning("cache.cleanup.failed", error=repr(exc))


__all__ = ["InMemoryQueryCache"]
