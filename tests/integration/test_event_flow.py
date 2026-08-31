"""Integration tests for the complete event publish → dispatch → consume flow."""

from __future__ import annotations

from eaip.app import ApplicationBuilder
from eaip.events.bus import EventBus
from eaip.events.dispatcher import EventDispatcher
from eaip.events.envelope import EventEnvelope
from eaip.events.event import DomainEvent
from eaip.events.hooks import EventHooks
from eaip.events.retry import FixedDelayRetry
from eaip.metrics.metrics import Meter


class OrderSubmitted(DomainEvent):
    event_type = "order.submitted"
    order_id: str
    amount: float


class OrderValidated(DomainEvent):
    event_type = "order.validated"
    order_id: str
    valid: bool


class OrderProcessed(DomainEvent):
    event_type = "order.processed"
    order_id: str
    processor: str


class TestEventFlow:
    """End-to-end event flow through the full EAIP stack."""

    async def test_publish_from_built_app(self):
        """Publish an event through a builder-constructed app."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        received: list[str] = []

        async def handler(event: OrderSubmitted) -> None:
            received.append(event.order_id)

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            dispatcher = EventDispatcher(bus)
            dispatcher.subscribe(OrderSubmitted, handler)

            result = await dispatcher.publish(
                OrderSubmitted(order_id="ord-001", amount=99.95),
            )

        assert received == ["ord-001"]
        assert result.handler_count == 1
        assert result.success_count == 1
        assert result.envelope.event_type == "order.submitted"

    async def test_chained_events_with_causation(self):
        """Publish a chain of causally-related events."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        chain: list[tuple[str, str | None]] = []

        async def on_submit(event: OrderSubmitted) -> None:
            chain.append(("submitted", None))

        async def on_validate(event: OrderValidated) -> None:
            chain.append(("validated", event.correlation_id))

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            dispatcher = EventDispatcher(bus)
            dispatcher.subscribe(OrderSubmitted, on_submit)
            dispatcher.subscribe(OrderValidated, on_validate)

            first = await dispatcher.publish(
                OrderSubmitted(order_id="ord-001", amount=50.0),
            )
            cid = first.envelope.correlation_id

            await dispatcher.publish(
                OrderValidated(order_id="ord-001", valid=True),
                causation_id=cid,
            )

        assert chain[0][0] == "submitted"
        assert chain[1][0] == "validated"

    async def test_retry_chain_with_fixed_delay(self):
        """Handler that fails then succeeds after retry."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        attempt_count: int = 0

        async def flaky_handler(event: OrderSubmitted) -> None:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("not ready yet")

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            dispatcher = EventDispatcher(
                bus,
                retry=FixedDelayRetry(delay=0.01, max_retries=2),
            )
            dispatcher.subscribe(OrderSubmitted, flaky_handler)

            result = await dispatcher.publish(
                OrderSubmitted(order_id="ord-001", amount=10.0),
            )

        assert attempt_count >= 2
        assert result.success_count == 1
        assert result.failure_count == 0

    async def test_hooks_integration(self):
        """Hooks are invoked at each lifecycle stage."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        stages: list[str] = []

        async def before_pub(envelope: EventEnvelope) -> EventEnvelope:
            stages.append("before_publish")
            return envelope

        async def after_pub(
            envelope: EventEnvelope,
            failures: list[tuple[str, BaseException]],
        ) -> None:
            stages.append("after_publish")

        hooks = EventHooks(
            before_publish=before_pub,
            after_publish=after_pub,
        )

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            dispatcher = EventDispatcher(bus, hooks=hooks)

            async def handler(event: OrderSubmitted) -> None:
                stages.append("handle")

            dispatcher.subscribe(OrderSubmitted, handler)
            await dispatcher.publish(OrderSubmitted(order_id="ord-001", amount=25.0))

        assert stages == ["before_publish", "handle", "after_publish"]

    async def test_metrics_integration_with_app(self):
        """Metrics are recorded through the app's Meter."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            meter: Meter = app.platform.container.resolve(Meter)
            dispatcher = EventDispatcher(bus, meter=meter)

            async def handler(event: OrderSubmitted) -> None:
                pass

            dispatcher.subscribe(OrderSubmitted, handler)

            # Publish 3 events
            for i in range(3):
                await dispatcher.publish(
                    OrderSubmitted(order_id=f"ord-{i:03d}", amount=float(i)),
                )

            published = meter.counter("event.published")
            assert published.value >= 3

    async def test_dispatcher_delegates_to_bus(self):
        """Dispatcher correctly delegates subscribe/unsubscribe to bus."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            dispatcher = EventDispatcher(bus)

            async def handler(event: OrderSubmitted) -> None:
                pass

            sub = dispatcher.subscribe(OrderSubmitted, handler)
            assert dispatcher.subscription_count == 1

            dispatcher.unsubscribe(sub)
            assert dispatcher.subscription_count == 0
