"""Tests for EventDispatcher."""

from __future__ import annotations

import pytest

from eaip.events.bus import EventBus
from eaip.events.dispatcher import EventDispatcher
from eaip.events.envelope import EventEnvelope
from eaip.events.event import DomainEvent
from eaip.events.hooks import EventHooks
from eaip.events.retry import ImmediateRetry
from eaip.metrics.metrics import Meter


class OrderPlaced(DomainEvent):
    event_type = "order.placed"
    order_id: str


class OrderShipped(DomainEvent):
    event_type = "order.shipped"
    order_id: str
    tracking: str


class TestEventDispatcher:
    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.fixture
    def dispatcher(self, bus):
        return EventDispatcher(bus)

    async def test_publish_delivers_to_subscribers(self, bus):
        dispatcher = EventDispatcher(bus)
        received: list[str] = []

        async def handler(event: OrderPlaced) -> None:
            received.append(event.order_id)

        dispatcher.subscribe(OrderPlaced, handler)
        result = await dispatcher.publish(OrderPlaced(order_id="ord-001"))

        assert received == ["ord-001"]
        assert result.handler_count == 1
        assert result.success_count == 1
        assert result.failure_count == 0

    async def test_publish_returns_envelope(self, bus):
        dispatcher = EventDispatcher(bus)

        result = await dispatcher.publish(OrderPlaced(order_id="ord-001"))
        assert isinstance(result.envelope, EventEnvelope)
        assert result.envelope.event_type == "order.placed"

    async def test_multiple_subscribers(self, bus):
        dispatcher = EventDispatcher(bus)
        received_1: list[str] = []
        received_2: list[str] = []

        async def handler_1(event: OrderPlaced) -> None:
            received_1.append(event.order_id)

        async def handler_2(event: OrderPlaced) -> None:
            received_2.append(event.order_id)

        dispatcher.subscribe(OrderPlaced, handler_1)
        dispatcher.subscribe(OrderPlaced, handler_2)
        result = await dispatcher.publish(OrderPlaced(order_id="ord-001"))

        assert received_1 == ["ord-001"]
        assert received_2 == ["ord-001"]
        assert result.handler_count == 2
        assert result.success_count == 2

    async def test_dispatcher_proxies_subscribe_unsubscribe(self, bus):
        dispatcher = EventDispatcher(bus)

        async def handler(event: OrderPlaced) -> None:
            pass

        sub = dispatcher.subscribe(OrderPlaced, handler)
        assert dispatcher.subscription_count == 1

        dispatcher.unsubscribe(sub)
        assert dispatcher.subscription_count == 0

    async def test_before_publish_hook(self, bus):
        transformed: list[str] = []

        async def tag_envelope(envelope: EventEnvelope) -> EventEnvelope:
            transformed.append("hook_called")
            return envelope.model_copy(update={"metadata": {**envelope.metadata, "tag": "test"}})

        hooks = EventHooks(before_publish=tag_envelope)
        dispatcher = EventDispatcher(bus, hooks=hooks)

        result = await dispatcher.publish(OrderPlaced(order_id="ord-001"))
        assert "hook_called" in transformed
        assert result.envelope.metadata.get("tag") == "test"

    async def test_after_publish_hook(self, bus):
        recorded: list[tuple[str, int]] = []

        async def record(
            envelope: EventEnvelope,
            failures: list[tuple[str, BaseException]],
        ) -> None:
            recorded.append((envelope.event_id, len(failures)))

        hooks = EventHooks(after_publish=record)
        dispatcher = EventDispatcher(bus, hooks=hooks)
        dispatcher.subscribe(OrderPlaced, lambda e: None)

        result = await dispatcher.publish(OrderPlaced(order_id="ord-001"))
        assert recorded[0][0] == result.envelope.event_id
        assert recorded[0][1] == 0

    async def test_retry_on_failure(self, bus):
        attempts: list[int] = []

        async def failing_handler(event: OrderPlaced) -> None:
            attempts.append(1)
            raise ValueError("handler failed")

        dispatcher = EventDispatcher(
            bus,
            retry=ImmediateRetry(max_retries=2),
        )
        dispatcher.subscribe(OrderPlaced, failing_handler)

        result = await dispatcher.publish(OrderPlaced(order_id="ord-001"))

        # 2 retries + 1 original = 3 total attempts, but success_count stays 0
        assert len(attempts) >= 2
        assert result.failure_count == 1
        assert result.retry_attempts >= 1

    async def test_metrics_integration(self, bus):
        meter = Meter(namespace="test")
        dispatcher = EventDispatcher(bus, meter=meter)

        async def handler(event: OrderPlaced) -> None:
            pass

        dispatcher.subscribe(OrderPlaced, handler)
        await dispatcher.publish(OrderPlaced(order_id="ord-001"))

        published_counter = meter.counter("event.published")
        assert published_counter.value >= 1

    async def test_publish_with_causation_id(self, bus):
        dispatcher = EventDispatcher(bus)
        result = await dispatcher.publish(
            OrderPlaced(order_id="ord-001"),
            causation_id="cause-abc",
        )

        assert result.envelope.causation_id == "cause-abc"

    async def test_sync_handler_supported(self, bus):
        dispatcher = EventDispatcher(bus)
        seen: list[str] = []

        def sync_handler(event: OrderPlaced) -> None:
            seen.append(event.order_id)

        dispatcher.subscribe(OrderPlaced, sync_handler)
        await dispatcher.publish(OrderPlaced(order_id="ord-001"))

        assert seen == ["ord-001"]

    async def test_no_subscribers_returns_empty_result(self, bus):
        dispatcher = EventDispatcher(bus)
        result = await dispatcher.publish(OrderPlaced(order_id="ord-001"))

        assert result.handler_count == 0
        assert result.success_count == 0
        assert result.failure_count == 0
