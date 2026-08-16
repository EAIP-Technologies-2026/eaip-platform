"""B01 — PersistentEventBus verification (persist → dispatch → dead-letter)."""

from __future__ import annotations

import pytest

from eaip.events.bus import EventBus
from eaip.events.deadletter import DeadLetterQueue
from eaip.events.event import DomainEvent
from eaip.events.persistent_bus import PersistentEventBus
from eaip.events.store_pg import PgEventStore


class _OrderPlaced(DomainEvent):
    event_type = "test.order_placed"
    order_id: str


class TestPersistentEventBus:
    def _make_bus(self) -> tuple[PersistentEventBus, PgEventStore, DeadLetterQueue]:
        store = PgEventStore()
        dlq = DeadLetterQueue()
        inner = EventBus()
        bus = PersistentEventBus(bus=inner, store=store, dead_letter=dlq)
        return bus, store, dlq

    async def test_publish_persists_event(self, db: None) -> None:
        bus, store, _ = self._make_bus()
        await bus.publish(_OrderPlaced(order_id="o1", tenant_id="acme"))
        assert await store.count() == 1
        assert await store.count(tenant_id="acme") == 1

    async def test_publish_dispatches_to_subscribers(self, db: None) -> None:
        bus, _, _ = self._make_bus()
        received: list[str] = []

        async def handler(evt: _OrderPlaced) -> None:
            received.append(evt.order_id)

        bus.subscribe(_OrderPlaced, handler)
        await bus.publish(_OrderPlaced(order_id="o1"))
        assert received == ["o1"]

    async def test_failing_handler_dead_lettered(self, db: None) -> None:
        bus, _, dlq = self._make_bus()

        async def bad(_evt: _OrderPlaced) -> None:
            raise ValueError("handler exploded")

        bus.subscribe(_OrderPlaced, bad)
        failures = await bus.publish(_OrderPlaced(order_id="o1"))
        assert len(failures) == 1
        assert await dlq.count() == 1
        letter = (await dlq.recent())[0]
        assert letter["event_type"] == "_OrderPlaced"
        assert letter["error_message"] == "handler exploded"

    async def test_event_still_persisted_when_handler_fails(self, db: None) -> None:
        bus, store, _ = self._make_bus()

        async def bad(_evt: _OrderPlaced) -> None:
            raise RuntimeError("boom")

        bus.subscribe(_OrderPlaced, bad)
        await bus.publish(_OrderPlaced(order_id="o1"))
        assert await store.count() == 1

    async def test_duplicate_publish_is_idempotent(self, db: None) -> None:
        bus, store, _ = self._make_bus()
        event = _OrderPlaced(order_id="o1")
        await bus.publish(event)
        await bus.publish(event)
        assert await store.count() == 1

    async def test_subscription_api_delegates(self, db: None) -> None:
        bus, _, _ = self._make_bus()
        token = bus.subscribe(_OrderPlaced, lambda _e: None)
        assert bus.unsubscribe(token) is True

    async def test_persist_failure_creates_dead_letter(self, db: None) -> None:
        class _FailingStore(PgEventStore):
            async def record(self, _event: DomainEvent) -> None:
                raise RuntimeError("db unavailable")

        store = _FailingStore()
        dlq = DeadLetterQueue()
        bus = PersistentEventBus(bus=EventBus(), store=store, dead_letter=dlq)
        await bus.publish(_OrderPlaced(order_id="o1"))
        assert await dlq.count() == 1
        letter = (await dlq.recent())[0]
        assert letter["handler_name"] == "persistent_bus.persist"