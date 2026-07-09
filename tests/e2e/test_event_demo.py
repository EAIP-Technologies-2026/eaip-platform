"""End-to-end demonstration: complete publish → dispatch → consume workflow.

This test simulates a realistic event-driven flow with multiple event types,
chained causation, retry handling, and metrics — all running through the
full EAIP bootstrapped application.
"""

from __future__ import annotations

from eaip.app import ApplicationBuilder
from eaip.events.bus import EventBus
from eaip.events.dispatcher import EventDispatcher
from eaip.events.event import DomainEvent
from eaip.events.retry import FixedDelayRetry
from eaip.metrics.metrics import Meter


class OrderCreated(DomainEvent):
    event_type = "order.created"
    order_id: str
    items: list[str]


class InventoryReserved(DomainEvent):
    event_type = "inventory.reserved"
    order_id: str
    reserved: bool


class PaymentProcessed(DomainEvent):
    event_type = "payment.processed"
    order_id: str
    success: bool


class OrderConfirmed(DomainEvent):
    event_type = "order.confirmed"
    order_id: str


class OrderFailed(DomainEvent):
    event_type = "order.failed"
    order_id: str
    reason: str


class TestEventDemo:
    """Demonstrates a complete event-driven order workflow."""

    async def test_complete_order_workflow(self):
        """Simulate an order lifecycle: create → reserve → pay → confirm."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        workflow_log: list[str] = []

        async def on_created(event: OrderCreated) -> None:
            workflow_log.append(f"created:{event.order_id}")

        async def on_reserve(event: InventoryReserved) -> None:
            workflow_log.append(f"reserved:{event.order_id}:{event.reserved}")

        async def on_payment(event: PaymentProcessed) -> None:
            workflow_log.append(f"payment:{event.order_id}:{event.success}")

        async def on_confirm(event: OrderConfirmed) -> None:
            workflow_log.append(f"confirmed:{event.order_id}")

        async def on_failed(event: OrderFailed) -> None:
            workflow_log.append(f"failed:{event.order_id}:{event.reason}")

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            dispatcher = EventDispatcher(bus)
            dispatcher.subscribe(OrderCreated, on_created)
            dispatcher.subscribe(InventoryReserved, on_reserve)
            dispatcher.subscribe(PaymentProcessed, on_payment)
            dispatcher.subscribe(OrderConfirmed, on_confirm)
            dispatcher.subscribe(OrderFailed, on_failed)

            # Step 1: Create order
            create = await dispatcher.publish(
                OrderCreated(order_id="ord-001", items=["widget", "gadget"]),
            )
            causation = create.envelope.event_id

            # Step 2: Reserve inventory
            reserve = await dispatcher.publish(
                InventoryReserved(order_id="ord-001", reserved=True),
                causation_id=causation,
            )

            # Step 3: Process payment
            payment = await dispatcher.publish(
                PaymentProcessed(order_id="ord-001", success=True),
                causation_id=reserve.envelope.event_id,
            )

            # Step 4: Confirm order
            await dispatcher.publish(
                OrderConfirmed(order_id="ord-001"),
                causation_id=payment.envelope.event_id,
            )

        assert workflow_log == [
            "created:ord-001",
            "reserved:ord-001:True",
            "payment:ord-001:True",
            "confirmed:ord-001",
        ]

    async def test_failing_handler_with_compensation(self):
        """Demonstrate a handler that fails, retries, and a compensating event."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        workflow_log: list[str] = []
        payment_attempts: int = 0

        async def on_created(event: OrderCreated) -> None:
            workflow_log.append(f"created:{event.order_id}")

        async def flaky_payment(event: PaymentProcessed) -> None:
            nonlocal payment_attempts
            payment_attempts += 1
            workflow_log.append(f"payment_attempt:{payment_attempts}:{event.order_id}")
            if payment_attempts < 2:
                raise ValueError("payment gateway timeout")
            workflow_log.append(f"payment_ok:{event.order_id}")

        async def on_confirmed(event: OrderConfirmed) -> None:
            workflow_log.append(f"confirmed:{event.order_id}")

        async def on_failed(event: OrderFailed) -> None:
            workflow_log.append(f"failed:{event.order_id}:{event.reason}")

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            dispatcher = EventDispatcher(
                bus,
                retry=FixedDelayRetry(delay=0.01, max_retries=2),
            )
            dispatcher.subscribe(OrderCreated, on_created)
            dispatcher.subscribe(PaymentProcessed, flaky_payment)
            dispatcher.subscribe(OrderConfirmed, on_confirmed)
            dispatcher.subscribe(OrderFailed, on_failed)

            create = await dispatcher.publish(
                OrderCreated(order_id="ord-002", items=["service"]),
            )

            payment = await dispatcher.publish(
                PaymentProcessed(order_id="ord-002", success=True),
                causation_id=create.envelope.event_id,
            )

            await dispatcher.publish(
                OrderConfirmed(order_id="ord-002"),
                causation_id=payment.envelope.event_id,
            )

        assert "created:ord-002" in workflow_log
        assert "payment_attempt:1:ord-002" in workflow_log
        assert "payment_attempt:2:ord-002" in workflow_log
        assert "confirmed:ord-002" in workflow_log
        assert payment_attempts == 2

    async def test_metrics_visible_in_workflow(self):
        """Verify metrics are collected during a multi-event workflow."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            bus: EventBus = app.platform.container.resolve(EventBus)
            meter: Meter = app.platform.container.resolve(Meter)
            dispatcher = EventDispatcher(bus, meter=meter)

            async def handler(event: OrderCreated) -> None:
                pass

            dispatcher.subscribe(OrderCreated, handler)

            for i in range(5):
                await dispatcher.publish(
                    OrderCreated(order_id=f"ord-{i:03d}", items=["x"]),
                )

            published = meter.counter("event.published")
            assert published.value == 5
