"""Domain events emitted by the caching subsystem."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class CacheHit(DomainEvent):
    """Emitted when a cache lookup succeeds."""

    event_type: ClassVar[str] = "eaip.cache.cache_hit"

    key: str
    namespace: str
    latency_ms: float


class CacheMiss(DomainEvent):
    """Emitted when a cache lookup fails to find a key."""

    event_type: ClassVar[str] = "eaip.cache.cache_miss"

    key: str
    namespace: str


class CacheEntryEvicted(DomainEvent):
    """Emitted when an entry is evicted from the cache."""

    event_type: ClassVar[str] = "eaip.cache.cache_entry_evicted"

    key: str
    namespace: str
    reason: str


class CacheCleared(DomainEvent):
    """Emitted when the entire cache namespace is cleared."""

    event_type: ClassVar[str] = "eaip.cache.cache_cleared"

    namespace: str
    entries_removed: int


class CacheEntryExpired(DomainEvent):
    """Emitted when a cached entry expires naturally."""

    event_type: ClassVar[str] = "eaip.cache.cache_entry_expired"

    key: str
    namespace: str
