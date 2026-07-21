"""Tests for cache domain events."""

from __future__ import annotations

import pydantic
import pytest

from eaip.cache.events import (
    CacheCleared,
    CacheEntryEvicted,
    CacheEntryExpired,
    CacheHit,
    CacheMiss,
)


class TestCacheHit:
    def test_create(self) -> None:
        event = CacheHit(key="k1", namespace="ns1", latency_ms=5.2)
        assert event.key == "k1"
        assert event.namespace == "ns1"
        assert event.latency_ms == 5.2
        assert event.event_type == "eaip.cache.cache_hit"

    def test_frozen(self) -> None:
        event = CacheHit(key="k", namespace="ns", latency_ms=1.0)
        with pytest.raises(pydantic.ValidationError):
            event.key = "new"  # type: ignore[misc]


class TestCacheMiss:
    def test_create(self) -> None:
        event = CacheMiss(key="k1", namespace="ns1")
        assert event.key == "k1"
        assert event.namespace == "ns1"
        assert event.event_type == "eaip.cache.cache_miss"


class TestCacheEntryEvicted:
    def test_create(self) -> None:
        event = CacheEntryEvicted(key="k1", namespace="ns1", reason="lru")
        assert event.key == "k1"
        assert event.reason == "lru"
        assert event.event_type == "eaip.cache.cache_entry_evicted"


class TestCacheCleared:
    def test_create(self) -> None:
        event = CacheCleared(namespace="ns1", entries_removed=42)
        assert event.namespace == "ns1"
        assert event.entries_removed == 42
        assert event.event_type == "eaip.cache.cache_cleared"


class TestCacheEntryExpired:
    def test_create(self) -> None:
        event = CacheEntryExpired(key="k1", namespace="ns1")
        assert event.key == "k1"
        assert event.namespace == "ns1"
        assert event.event_type == "eaip.cache.cache_entry_expired"
