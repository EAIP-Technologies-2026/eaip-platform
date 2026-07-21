"""In-memory repository implementing :class:`eaip.interfaces.repository.AbstractRepository`.

Provides a bounded, TTL-aware in-memory store with LRU eviction and hit/miss
metrics.  Designed as a drop-in replacement for ad-hoc ``dict`` usage across
capability services.

Usage::

    from eaip.shared.repository import InMemoryRepository

    repo: InMemoryRepository[str, MyModel] = InMemoryRepository(
        max_size=1000, default_ttl_seconds=3600,
    )
    await repo.add(my_model, ttl_seconds=300)
    found = await repo.get(my_model.id)
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from eaip.interfaces.repository import AbstractRepository

ID = TypeVar("ID")
T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    value: T
    expires_at: float = field(default=0.0)  # 0.0 means no expiry


class InMemoryRepository(AbstractRepository[ID, T]):
    """Bounded, TTL-aware in-memory repository with LRU eviction and metrics.

    Implements :class:`AbstractRepository` using an ``OrderedDict`` for
    O(1) lookups and LRU-ordered iteration.  Expired entries are skipped
    during :meth:`get` and a background :meth:`cleanup_expired` pass.

    Metrics are exposed via :meth:`get_stats` and individual counters.
    """

    def __init__(
        self,
        max_size: int = 10_000,
        default_ttl_seconds: float | None = None,
    ) -> None:
        """Initialise the repository.

        Args:
            max_size: Maximum number of entries before LRU eviction.
            default_ttl_seconds: Default TTL in seconds for entries added
                without an explicit ``ttl_seconds``. ``None`` means no TTL.
        """
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._max_size = max_size
        self._default_ttl_seconds = default_ttl_seconds
        self._store: OrderedDict[ID, _Entry[T]] = OrderedDict()
        self._hit_count: int = 0
        self._miss_count: int = 0
        self._eviction_count: int = 0
        self._cleanup_count: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get(self, identifier: ID) -> T | None:
        """Return the entry for *identifier*, or ``None`` if missing/expired.

        Moves the entry to the end of the LRU ordering on access.
        """
        entry = self._store.get(identifier)
        if entry is None:
            self._miss_count += 1
            return None

        if self._is_expired(entry):
            self._store.pop(identifier, None)
            self._miss_count += 1
            return None

        self._store.move_to_end(identifier)
        self._hit_count += 1
        return entry.value

    async def add(self, entity: T, ttl_seconds: float | None = None) -> None:
        """Persist *entity*, evicting LRU entries if at capacity.

        Args:
            entity: The entity to store.  Its ``id`` attribute is used as key.
            ttl_seconds: Optional TTL override.  Falls back to
                ``default_ttl_seconds``, then no expiry.
        """
        identifier: ID = entity.id  # type: ignore[attr-defined]
        self._store[identifier] = _Entry(
            value=entity,
            expires_at=_compute_expiry(ttl_seconds or self._default_ttl_seconds),
        )
        self._store.move_to_end(identifier)

        while len(self._store) > self._max_size:
            self._store.popitem(last=False)
            self._eviction_count += 1

    async def remove(self, identifier: ID) -> bool:
        """Delete the entry; return ``True`` if it existed."""
        if identifier in self._store:
            del self._store[identifier]
            return True
        return False

    async def iter_all(self) -> AsyncIterator[T]:
        """Yield every non-expired entry.

        Uses a snapshot when expired entries are detected; otherwise iterates
        in-place for zero-copy reads.
        """
        expired: list[ID] = []
        has_expired = False
        for ident, entry in list(self._store.items()):
            if self._is_expired(entry):
                expired.append(ident)
                has_expired = True
            else:
                yield entry.value
        if has_expired:
            for ident in expired:
                self._store.pop(ident, None)

    async def clear(self) -> None:
        """Remove all entries and reset metrics."""
        self._store.clear()
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0

    async def cleanup_expired(self) -> int:
        """Remove every expired entry and return the count removed."""
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if v.expires_at > 0 and now >= v.expires_at]
        for k in expired:
            del self._store[k]
        removed = len(expired)
        self._cleanup_count += removed
        return removed

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def hit_count(self) -> int:
        return self._hit_count

    @property
    def miss_count(self) -> int:
        return self._miss_count

    @property
    def eviction_count(self) -> int:
        return self._eviction_count

    @property
    def cleanup_count(self) -> int:
        return self._cleanup_count

    def get_stats(self) -> dict[str, Any]:
        """Return a snapshot of repository metrics."""
        total = self._hit_count + self._miss_count
        hit_rate = round(self._hit_count / total * 100, 2) if total > 0 else 0.0
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_pct": hit_rate,
            "eviction_count": self._eviction_count,
            "cleanup_count": self._cleanup_count,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_expired(entry: _Entry[T]) -> bool:
        if entry.expires_at <= 0:
            return False
        return time.monotonic() >= entry.expires_at


def _compute_expiry(ttl_seconds: float | None) -> float:
    """Return the absolute expiry timestamp (monotonic) or 0.0 for no expiry."""
    if ttl_seconds is not None and ttl_seconds > 0:
        return time.monotonic() + ttl_seconds
    return 0.0


__all__ = ["InMemoryRepository"]
