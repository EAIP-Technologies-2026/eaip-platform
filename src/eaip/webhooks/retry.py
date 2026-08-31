"""Exponential-backoff retry queue for failed webhook deliveries."""

from __future__ import annotations

import random
from datetime import timedelta

from eaip.shared.time import utc_now
from eaip.webhooks.models import WebhookConfig, WebhookDelivery


class RetryQueueService:
    """Schedules and processes retries for failed webhook deliveries."""

    def __init__(self, config: WebhookConfig | None = None) -> None:
        self._config = config or WebhookConfig()
        self._queue: dict[str, WebhookDelivery] = {}
        self._completed: set[str] = set()

    async def enqueue(self, delivery: WebhookDelivery) -> WebhookDelivery:
        delay = self._compute_delay(delivery.attempt)
        next_retry = utc_now() + timedelta(seconds=delay)
        updated = delivery.model_copy(update={"next_retry_at": next_retry})
        self._queue[updated.id] = updated
        return updated

    async def dequeue(self) -> WebhookDelivery | None:
        now = utc_now()
        for delivery_id, delivery in list(self._queue.items()):
            if delivery.next_retry_at and delivery.next_retry_at <= now:
                del self._queue[delivery_id]
                return delivery
        return None

    async def process_queue(self) -> list[WebhookDelivery]:
        now = utc_now()
        due: list[WebhookDelivery] = []
        for delivery_id, delivery in list(self._queue.items()):
            if delivery.next_retry_at and delivery.next_retry_at <= now:
                del self._queue[delivery_id]
                due.append(delivery)
        return due

    async def get_queue_depth(self) -> int:
        return len(self._queue)

    async def clear_completed(self) -> int:
        count = len(self._completed)
        self._completed.clear()
        return count

    def _compute_delay(self, attempt: int) -> float:
        base = self._config.default_retry_delay_seconds * (
            self._config.backoff_multiplier ** (attempt - 1)
        )
        capped = min(base, self._config.max_backoff_seconds)
        jitter = random.uniform(0, capped * 0.1)
        return capped + jitter


__all__ = ["RetryQueueService"]
