"""Domain events for cache invalidation."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class CacheInvalidated(DomainEvent):
    """Emitted when a cache entry is invalidated."""

    event_type: ClassVar[str] = "eaip.cacheinv.invalidated"

    request_id: str
    tag: str
    pattern: str


class CachePurged(DomainEvent):
    """Emitted when all cache entries for a tag are purged."""

    event_type: ClassVar[str] = "eaip.cacheinv.purged"

    tag: str
    entries_removed: int


class BulkInvalidationCompleted(DomainEvent):
    """Emitted when a bulk invalidation operation completes."""

    event_type: ClassVar[str] = "eaip.cacheinv.bulk_completed"

    request_id: str
    total_invalidated: int
    duration_ms: int


__all__ = [
    "BulkInvalidationCompleted",
    "CacheInvalidated",
    "CachePurged",
]
