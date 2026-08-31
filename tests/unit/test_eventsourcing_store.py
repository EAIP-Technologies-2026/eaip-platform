"""Tests for EventStore."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.eventsourcing.exceptions import EventStoreError
from eaip.eventsourcing.models import StoredEvent
from eaip.eventsourcing.store import EventStore


class TestEventStore:
    def test_append_and_get_events(self) -> None:
        store = EventStore()
        stored = store.append_event("order", "123", {"event_type": "order.created", "amount": 100})
        assert stored.aggregate_type == "order"
        assert stored.aggregate_id == "123"
        assert stored.event_type == "order.created"
        assert stored.version == 1

        events = store.get_events("order", "123")
        assert len(events) == 1
        assert events[0].id == stored.id

    def test_append_multiple_events_increments_version(self) -> None:
        store = EventStore()
        store.append_event("order", "123", {"event_type": "order.created"})
        e2 = store.append_event("order", "123", {"event_type": "order.shipped"})
        assert e2.version == 2
        e3 = store.append_event("order", "123", {"event_type": "order.delivered"})
        assert e3.version == 3

    def test_get_events_returns_in_order(self) -> None:
        store = EventStore()
        store.append_event("order", "123", {"event_type": "order.created"})
        store.append_event("order", "123", {"event_type": "order.shipped"})
        store.append_event("order", "123", {"event_type": "order.delivered"})
        events = store.get_events("order", "123")
        assert [e.event_type for e in events] == [
            "order.created",
            "order.shipped",
            "order.delivered",
        ]

    def test_get_events_empty_aggregate(self) -> None:
        store = EventStore()
        assert store.get_events("unknown", "999") == []

    def test_get_event_stream(self) -> None:
        store = EventStore()
        store.append_event("order", "123", {"event_type": "order.created"})
        store.append_event("order", "123", {"event_type": "order.shipped"})
        stream = store.get_event_stream("order", "123")
        assert stream.aggregate_type == "order"
        assert stream.aggregate_id == "123"
        assert stream.current_version == 2
        assert len(stream.events) == 2

    def test_get_event_stream_empty(self) -> None:
        store = EventStore()
        stream = store.get_event_stream("order", "999")
        assert stream.current_version == 0
        assert stream.events == ()

    def test_get_events_by_type(self) -> None:
        store = EventStore()
        store.append_event("order", "1", {"event_type": "order.created"})
        store.append_event("invoice", "1", {"event_type": "invoice.paid"})
        store.append_event("order", "2", {"event_type": "order.created"})
        events = store.get_events_by_type("order.created")
        assert len(events) == 2

    def test_get_events_by_type_with_since(self) -> None:
        store = EventStore()
        store.append_event("order", "1", {"event_type": "order.created"})
        later = datetime.now(UTC) + timedelta(hours=1)
        events = store.get_events_by_type("order.created", since=later)
        assert len(events) == 0

    def test_get_aggregate_ids(self) -> None:
        store = EventStore()
        store.append_event("order", "a", {"event_type": "order.created"})
        store.append_event("order", "b", {"event_type": "order.created"})
        store.append_event("invoice", "c", {"event_type": "invoice.paid"})
        ids = store.get_aggregate_ids("order")
        assert sorted(ids) == ["a", "b"]

    def test_get_aggregate_ids_empty(self) -> None:
        store = EventStore()
        assert store.get_aggregate_ids("nobody") == []

    def test_get_events_since(self) -> None:
        store = EventStore()
        e1 = store.append_event("order", "1", {"event_type": "order.created"})
        e2 = store.append_event("order", "1", {"event_type": "order.shipped"})
        events = store.get_events_since(e1.id)
        assert len(events) == 1
        assert events[0].id == e2.id

    def test_get_events_since_unknown(self) -> None:
        store = EventStore()
        with pytest.raises(EventStoreError):
            store.get_events_since("does-not-exist")

    def test_append_stored_event_object(self) -> None:
        store = EventStore()
        original = StoredEvent(
            id="pre-1",
            aggregate_type="order",
            aggregate_id="123",
            event_type="order.created",
            event_data={"amount": 50},
            correlation_id="corr-x",
        )
        stored = store.append_event("order", "123", original)
        assert stored.id == "pre-1"
        assert stored.event_type == "order.created"
        assert stored.event_data == {"amount": 50}
        assert stored.correlation_id == "corr-x"

    def test_count_events(self) -> None:
        store = EventStore()
        assert store.count_events() == 0
        store.append_event("order", "1", {"event_type": "order.created"})
        assert store.count_events() == 1
        store.append_event("order", "1", {"event_type": "order.shipped"})
        assert store.count_events() == 2

    def test_get_event_by_id(self) -> None:
        store = EventStore()
        stored = store.append_event("order", "1", {"event_type": "order.created"})
        assert store.get_event_by_id(stored.id) is stored
        assert store.get_event_by_id("nope") is None

    def test_append_with_metadata(self) -> None:
        store = EventStore()
        stored = store.append_event(
            "order", "1", {"event_type": "order.created"}, metadata={"source": "api"}
        )
        assert stored.metadata == {"source": "api"}

    def test_append_with_correlation_and_causation(self) -> None:
        store = EventStore()
        stored = store.append_event(
            "order",
            "1",
            {"event_type": "order.created"},
            correlation_id="corr-1",
            causation_id="caus-1",
        )
        assert stored.correlation_id == "corr-1"
        assert stored.causation_id == "caus-1"

    def test_separate_aggregates_dont_mix(self) -> None:
        store = EventStore()
        store.append_event("order", "1", {"event_type": "order.created"})
        store.append_event("invoice", "1", {"event_type": "invoice.paid"})
        assert len(store.get_events("order", "1")) == 1
        assert len(store.get_events("invoice", "1")) == 1
