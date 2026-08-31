"""Tests for TriggerService."""

from __future__ import annotations

import pytest

from eaip.automation.models import TriggerEvent
from eaip.automation.triggers import TriggerService
from eaip.events.bus import EventBus


class TestTriggerService:
    @pytest.fixture
    def service(self) -> TriggerService:
        return TriggerService()

    @pytest.fixture
    def event_bus(self) -> EventBus:
        return EventBus()

    async def test_process_event_dispatches_to_listeners(self, service) -> None:
        received: list[str] = []

        async def handler(event: TriggerEvent) -> None:
            received.append(event.type)

        service.register_event_listener("order.created", handler)
        event = TriggerEvent(id="evt1", type="order.created", source="shopify")
        await service.process_event(event)
        assert received == ["order.created"]

    async def test_process_event_multiple_listeners(self, service) -> None:
        received: list[str] = []

        async def handler1(event: TriggerEvent) -> None:
            received.append("h1")

        async def handler2(event: TriggerEvent) -> None:
            received.append("h2")

        service.register_event_listener("order.created", handler1)
        service.register_event_listener("order.created", handler2)
        event = TriggerEvent(id="evt1", type="order.created", source="shopify")
        await service.process_event(event)
        assert len(received) == 2

    async def test_process_event_wildcard_listener(self, service) -> None:
        received: list[str] = []

        async def handler(event: TriggerEvent) -> None:
            received.append(event.type)

        service.register_event_listener("*", handler)
        event = TriggerEvent(id="evt1", type="any.event", source="test")
        await service.process_event(event)
        assert received == ["any.event"]

    async def test_process_event_no_listeners(self, service) -> None:
        event = TriggerEvent(id="evt1", type="unregistered", source="test")
        await service.process_event(event)

    async def test_process_event_handler_exception(self, service) -> None:
        async def failing_handler(event: TriggerEvent) -> None:
            raise ValueError("Handler error")

        service.register_event_listener("test", failing_handler)
        event = TriggerEvent(id="evt1", type="test", source="test")
        await service.process_event(event)

    async def test_create_trigger_event(self, service) -> None:
        event = await service.create_trigger_event(
            "order.created",
            payload={"order_id": "123"},
            source="shopify",
            correlation_id="corr-123",
            metadata={"env": "prod"},
        )
        assert event.type == "order.created"
        assert event.payload == {"order_id": "123"}
        assert event.source == "shopify"
        assert event.correlation_id == "corr-123"
        assert event.metadata == {"env": "prod"}
        assert event.id is not None

    async def test_create_trigger_event_defaults(self, service) -> None:
        event = await service.create_trigger_event("test.event", {"key": "value"})
        assert event.source == "automation"
        assert event.correlation_id == ""

    async def test_register_listener(self, service) -> None:
        def handler(event: TriggerEvent) -> None:
            pass

        service.register_event_listener("test", handler)
        assert "test" in service._listeners
        assert handler in service._listeners["test"]

    async def test_unregister_listener(self, service) -> None:
        def handler(event: TriggerEvent) -> None:
            pass

        service.register_event_listener("test", handler)
        service.unregister_event_listener("test", handler)
        assert handler not in service._listeners.get("test", [])

    async def test_unregister_nonexistent_listener(self, service) -> None:
        def handler(event: TriggerEvent) -> None:
            pass

        service.unregister_event_listener("nonexistent", handler)

    async def test_check_scheduled_rules_empty(self, service) -> None:
        events = await service.check_scheduled_rules()
        assert events == []

    async def test_process_event_with_sync_handler(self, service) -> None:
        received: list[str] = []

        def handler(event: TriggerEvent) -> None:
            received.append(event.type)

        service.register_event_listener("test", handler)
        event = TriggerEvent(id="evt1", type="test", source="test")
        await service.process_event(event)
        assert received == ["test"]

    async def test_create_trigger_event_multiple(self, service) -> None:
        events = []
        for i in range(5):
            event = await service.create_trigger_event(f"type.{i}", {"idx": i})
            events.append(event)
        assert len(events) == 5
        assert all(e.id for e in events)
        assert events[0].type != events[1].type
