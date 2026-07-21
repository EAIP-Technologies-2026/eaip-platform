"""Tests for webhook retry queue service."""

from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.shared.time import utc_now
from eaip.webhooks.models import DeliveryStatus, WebhookConfig, WebhookDelivery
from eaip.webhooks.retry import RetryQueueService


class TestRetryQueueService:
    def make_delivery(self, delivery_id: str = "d1", attempt: int = 1) -> WebhookDelivery:
        return WebhookDelivery(
            id=delivery_id,
            endpoint_id="ep1",
            event_type="test.event",
            payload={},
            status=DeliveryStatus.RETRYING,
            attempt=attempt,
            max_attempts=3,
        )

    @pytest.mark.asyncio
    async def test_enqueue_sets_next_retry_at(self) -> None:
        svc = RetryQueueService()
        d = self.make_delivery()
        enqueued = await svc.enqueue(d)
        assert enqueued.next_retry_at is not None
        assert enqueued.next_retry_at > utc_now()

    @pytest.mark.asyncio
    async def test_dequeue_returns_none_when_empty(self) -> None:
        svc = RetryQueueService()
        assert await svc.dequeue() is None

    @pytest.mark.asyncio
    async def test_dequeue_returns_due_delivery(self) -> None:
        svc = RetryQueueService()
        d = self.make_delivery()
        enqueued = await svc.enqueue(d)
        # Manually set next_retry_at to the past
        past = utc_now() - timedelta(seconds=10)
        enqueued = enqueued.model_copy(update={"next_retry_at": past})
        svc._queue[enqueued.id] = enqueued
        result = await svc.dequeue()
        assert result is not None
        assert result.id == "d1"

    @pytest.mark.asyncio
    async def test_get_queue_depth(self) -> None:
        svc = RetryQueueService()
        assert await svc.get_queue_depth() == 0
        await svc.enqueue(self.make_delivery("d1"))
        await svc.enqueue(self.make_delivery("d2"))
        assert await svc.get_queue_depth() == 2

    @pytest.mark.asyncio
    async def test_process_queue_returns_due_deliveries(self) -> None:
        svc = RetryQueueService()
        d1 = await svc.enqueue(self.make_delivery("d1"))
        d2 = await svc.enqueue(self.make_delivery("d2"))
        past = utc_now() - timedelta(seconds=10)
        svc._queue["d1"] = d1.model_copy(update={"next_retry_at": past})
        svc._queue["d2"] = d2.model_copy(update={"next_retry_at": past})
        due = await svc.process_queue()
        assert len(due) == 2
        assert await svc.get_queue_depth() == 0

    @pytest.mark.asyncio
    async def test_clear_completed(self) -> None:
        svc = RetryQueueService()
        svc._completed.add("d1")
        svc._completed.add("d2")
        assert await svc.clear_completed() == 2
        assert await svc.clear_completed() == 0

    @pytest.mark.asyncio
    async def test_exponential_backoff(self) -> None:
        svc = RetryQueueService()
        # Attempt 1: base ~60s
        d1 = await svc.enqueue(self.make_delivery("d1", attempt=1))
        delay1 = (d1.next_retry_at - utc_now()).total_seconds() if d1.next_retry_at else 0
        # Attempt 2: base ~120s
        d2 = await svc.enqueue(self.make_delivery("d2", attempt=2))
        delay2 = (d2.next_retry_at - utc_now()).total_seconds() if d2.next_retry_at else 0
        assert delay2 > delay1

    @pytest.mark.asyncio
    async def test_backoff_capped_by_max(self) -> None:
        config = WebhookConfig(
            default_retry_delay_seconds=1, backoff_multiplier=10000, max_backoff_seconds=3600
        )
        svc = RetryQueueService(config=config)
        d = await svc.enqueue(self.make_delivery("d1", attempt=2))
        delay = (d.next_retry_at - utc_now()).total_seconds() if d.next_retry_at else 0
        assert delay <= 3600 + (3600 * 0.1)  # max + jitter

    @pytest.mark.asyncio
    async def test_enqueue_multiple_deliveries(self) -> None:
        svc = RetryQueueService()
        for i in range(5):
            await svc.enqueue(self.make_delivery(f"d{i}", attempt=1))
        assert await svc.get_queue_depth() == 5
