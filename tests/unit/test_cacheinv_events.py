"""Tests for cacheinv domain events."""

from __future__ import annotations

from eaip.cacheinv.events import BulkInvalidationCompleted, CacheInvalidated, CachePurged
from eaip.events.event import DomainEvent


class TestCacheInvalidated:
    def test_event_type(self) -> None:
        event = CacheInvalidated(request_id="req1", tag="users", pattern="users:*")
        assert event.event_type == "eaip.cacheinv.invalidated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = CacheInvalidated(request_id="req1", tag="users", pattern="users:*")
        assert event.request_id == "req1"
        assert event.tag == "users"
        assert event.pattern == "users:*"


class TestCachePurged:
    def test_event_type(self) -> None:
        event = CachePurged(tag="users", entries_removed=42)
        assert event.event_type == "eaip.cacheinv.purged"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = CachePurged(tag="users", entries_removed=42)
        assert event.tag == "users"
        assert event.entries_removed == 42


class TestBulkInvalidationCompleted:
    def test_event_type(self) -> None:
        event = BulkInvalidationCompleted(request_id="bulk1", total_invalidated=100, duration_ms=50)
        assert event.event_type == "eaip.cacheinv.bulk_completed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = BulkInvalidationCompleted(request_id="bulk1", total_invalidated=100, duration_ms=50)
        assert event.request_id == "bulk1"
        assert event.total_invalidated == 100
        assert event.duration_ms == 50


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(CacheInvalidated, DomainEvent)
        assert issubclass(CachePurged, DomainEvent)
        assert issubclass(BulkInvalidationCompleted, DomainEvent)
