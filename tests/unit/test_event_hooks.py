"""Tests for event lifecycle hooks."""

from __future__ import annotations

from eaip.events.envelope import EventEnvelope
from eaip.events.event import DomainEvent
from eaip.events.hooks import EventHooks


class OrderPlaced(DomainEvent):
    event_type = "order.placed"
    order_id: str


class TestEventHooks:
    async def test_before_publish_can_transform_envelope(self):
        async def add_tag(envelope: EventEnvelope) -> EventEnvelope:
            return envelope.model_copy(update={"metadata": {**envelope.metadata, "tag": "test"}})

        hooks = EventHooks(before_publish=add_tag)
        event = OrderPlaced(order_id="ord-001")
        envelope = EventEnvelope.from_event(event)

        result = await hooks.before_publish(envelope)
        assert result.metadata["tag"] == "test"

    async def test_after_publish_receives_failures(self):
        recorded: list[tuple[str, list]] = []

        async def record(
            envelope: EventEnvelope,
            failures: list[tuple[str, BaseException]],
        ) -> None:
            recorded.append((envelope.event_id, failures))

        hooks = EventHooks(after_publish=record)
        event = OrderPlaced(order_id="ord-001")
        envelope = EventEnvelope.from_event(event)

        await hooks.after_publish(envelope, [("sub-1", ValueError("bad"))])
        assert recorded[0][0] == envelope.event_id
        assert len(recorded[0][1]) == 1

    async def test_before_handle_can_skip_handler(self):
        async def always_skip(
            envelope: EventEnvelope,
            handler_id: str,
        ) -> bool:
            return False

        hooks = EventHooks(before_handle=always_skip)
        event = OrderPlaced(order_id="ord-001")
        envelope = EventEnvelope.from_event(event)

        result = await hooks.before_handle(envelope, "handler-1")
        assert result is False

    async def test_after_handle_records_exception(self):
        recorded: list[tuple[str, str, BaseException | None]] = []

        async def record(
            envelope: EventEnvelope,
            handler_id: str,
            exception: BaseException | None,
        ) -> None:
            recorded.append((envelope.event_id, handler_id, exception))

        hooks = EventHooks(after_handle=record)
        event = OrderPlaced(order_id="ord-001")
        envelope = EventEnvelope.from_event(event)
        exc = ValueError("oops")

        await hooks.after_handle(envelope, "h-1", exc)
        assert recorded[0][2] is exc

        await hooks.after_handle(envelope, "h-2", None)
        assert recorded[1][2] is None

    async def test_all_hooks_optional(self):
        hooks = EventHooks()
        assert hooks.before_publish is None
        assert hooks.after_publish is None
        assert hooks.before_handle is None
        assert hooks.after_handle is None
        assert hooks.on_error is None
