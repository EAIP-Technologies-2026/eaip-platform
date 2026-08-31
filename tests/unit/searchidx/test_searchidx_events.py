from __future__ import annotations

import pydantic
import pytest

from eaip.searchidx.events import (
    CacheHit,
    CacheInvalidated,
    CacheMiss,
    CacheWarmingCompleted,
    CacheWarmingStarted,
    IndexBuildCompleted,
    IndexBuildFailed,
    IndexBuildStarted,
    IndexCreated,
    IndexDeleted,
    SearchIndexEvent,
)


class TestSearchidxEvents:
    def test_base_event(self) -> None:
        assert SearchIndexEvent.event_type == "eaip.searchidx.event"

    def test_index_created(self) -> None:
        event = IndexCreated(index_id="idx1", name="articles", source_type="docs")
        assert event.event_type == "eaip.searchidx.index.created"
        assert event.index_id == "idx1"

    def test_index_deleted(self) -> None:
        event = IndexDeleted(index_id="idx1", name="articles")
        assert event.event_type == "eaip.searchidx.index.deleted"

    def test_index_build_started(self) -> None:
        event = IndexBuildStarted(index_id="idx1", job_id="j1", job_type="full")
        assert event.event_type == "eaip.searchidx.index.build_started"
        assert event.job_type == "full"

    def test_index_build_started_default_type(self) -> None:
        event = IndexBuildStarted(index_id="idx1", job_id="j1")
        assert event.job_type == "full"

    def test_index_build_completed(self) -> None:
        event = IndexBuildCompleted(index_id="idx1", job_id="j1", documents_processed=500)
        assert event.event_type == "eaip.searchidx.index.build_completed"
        assert event.documents_processed == 500

    def test_index_build_failed(self) -> None:
        event = IndexBuildFailed(index_id="idx1", job_id="j1", error="timeout")
        assert event.event_type == "eaip.searchidx.index.build_failed"
        assert event.error == "timeout"

    def test_cache_hit(self) -> None:
        event = CacheHit(key="mykey", ttl_ms=12.5)
        assert event.event_type == "eaip.searchidx.cache.hit"
        assert event.ttl_ms == 12.5

    def test_cache_miss(self) -> None:
        event = CacheMiss(key="mykey")
        assert event.event_type == "eaip.searchidx.cache.miss"

    def test_cache_invalidated(self) -> None:
        event = CacheInvalidated(pattern="idx:*", entries_removed=5)
        assert event.event_type == "eaip.searchidx.cache.invalidated"
        assert event.entries_removed == 5

    def test_cache_warming_started(self) -> None:
        event = CacheWarmingStarted(keys_count=100)
        assert event.event_type == "eaip.searchidx.cache.warming_started"

    def test_cache_warming_completed(self) -> None:
        event = CacheWarmingCompleted(keys_warmed=100, duration_ms=500.0)
        assert event.event_type == "eaip.searchidx.cache.warming_completed"

    def test_all_frozen(self) -> None:
        event = IndexCreated(index_id="idx1", name="articles", source_type="docs")
        with pytest.raises(pydantic.ValidationError):
            event.index_id = "idx2"  # type: ignore[misc]
