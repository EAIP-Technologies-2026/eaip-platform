"""Search index domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class SearchIndexEvent(DomainEvent):
    """Base event for all search index events."""

    event_type: ClassVar[str] = "eaip.searchidx.event"


class IndexCreated(SearchIndexEvent):
    """Published when a search index is created."""

    event_type: ClassVar[str] = "eaip.searchidx.index.created"
    index_id: str
    name: str
    source_type: str


class IndexDeleted(SearchIndexEvent):
    """Published when a search index is deleted."""

    event_type: ClassVar[str] = "eaip.searchidx.index.deleted"
    index_id: str
    name: str


class IndexBuildStarted(SearchIndexEvent):
    """Published when an index build job starts."""

    event_type: ClassVar[str] = "eaip.searchidx.index.build_started"
    index_id: str
    job_id: str
    job_type: str = "full"


class IndexBuildCompleted(SearchIndexEvent):
    """Published when an index build completes successfully."""

    event_type: ClassVar[str] = "eaip.searchidx.index.build_completed"
    index_id: str
    job_id: str
    documents_processed: int = 0


class IndexBuildFailed(SearchIndexEvent):
    """Published when an index build fails."""

    event_type: ClassVar[str] = "eaip.searchidx.index.build_failed"
    index_id: str
    job_id: str
    error: str = ""


class CacheHit(SearchIndexEvent):
    """Published on a successful cache lookup."""

    event_type: ClassVar[str] = "eaip.searchidx.cache.hit"
    key: str
    ttl_ms: float = 0.0


class CacheMiss(SearchIndexEvent):
    """Published when a cache key is not found."""

    event_type: ClassVar[str] = "eaip.searchidx.cache.miss"
    key: str


class CacheInvalidated(SearchIndexEvent):
    """Published when a cache entry is invalidated."""

    event_type: ClassVar[str] = "eaip.searchidx.cache.invalidated"
    pattern: str
    entries_removed: int = 0


class CacheWarmingStarted(SearchIndexEvent):
    """Published when cache warming begins."""

    event_type: ClassVar[str] = "eaip.searchidx.cache.warming_started"
    keys_count: int = 0


class CacheWarmingCompleted(SearchIndexEvent):
    """Published when cache warming finishes."""

    event_type: ClassVar[str] = "eaip.searchidx.cache.warming_completed"
    keys_warmed: int = 0
    duration_ms: float = 0.0


__all__ = [
    "CacheHit",
    "CacheInvalidated",
    "CacheMiss",
    "CacheWarmingCompleted",
    "CacheWarmingStarted",
    "IndexBuildCompleted",
    "IndexBuildFailed",
    "IndexBuildStarted",
    "IndexCreated",
    "IndexDeleted",
    "SearchIndexEvent",
]
