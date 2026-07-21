"""Queue manager — create, delete, list, and route messages between queues."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.queue.exceptions import QueueError
from eaip.queue.models import QueueConfig, QueueMessage, QueueStats
from eaip.queue.provider import InMemoryQueue, MessageQueue


class QueueManager:
    """Manage multiple queues, including DLQ routing."""

    def __init__(self, event_bus: Any = None) -> None:
        """Initialize the queue manager."""
        self._queues: dict[str, MessageQueue] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.queue.manager")

    def create_queue(self, config: QueueConfig) -> MessageQueue:
        """Create a new queue with the given configuration."""
        if config.name in self._queues:
            raise QueueError(f"Queue '{config.name}' already exists")
        queue = InMemoryQueue(config, event_bus=self._event_bus)
        self._queues[config.name] = queue

        if config.dead_letter_queue and config.dead_letter_queue not in self._queues:
            dlq_config = QueueConfig(
                name=config.dead_letter_queue,
                max_size=config.max_size,
            )
            self._queues[config.dead_letter_queue] = InMemoryQueue(
                dlq_config, event_bus=self._event_bus
            )

        self._log.info("queue.created", name=config.name)
        return queue

    def get_queue(self, name: str) -> MessageQueue | None:
        """Retrieve a queue by name."""
        return self._queues.get(name)

    def delete_queue(self, name: str) -> bool:
        """Delete a queue and return True on success."""
        queue = self._queues.pop(name, None)
        if queue is None:
            return False
        self._log.info("queue.deleted", name=name)
        return True

    def list_queues(self) -> list[str]:
        """Return the names of all managed queues."""
        return list(self._queues.keys())

    async def enqueue_to(self, queue_name: str, message: QueueMessage) -> None:
        """Enqueue a message to a specific queue."""
        queue = self._queues.get(queue_name)
        if queue is None:
            raise QueueError(f"Queue '{queue_name}' not found")
        await queue.enqueue(message)

    async def route_message(self, source: str, target: str, message_id: str) -> bool:
        """Route a message from source queue to target queue."""
        src_queue = self._queues.get(source)
        if src_queue is None:
            raise QueueError(f"Source queue '{source}' not found")

        tgt_queue = self._queues.get(target)
        if tgt_queue is None:
            raise QueueError(f"Target queue '{target}' not found")

        msg = await src_queue.dequeue("router", timeout=5.0)
        if msg is None or msg.message_id != message_id:
            return False

        await tgt_queue.enqueue(msg)
        self._log.info("queue.routed", source=source, target=target, message_id=message_id)
        return True

    async def get_dlq_messages(self, queue_name: str) -> list[QueueMessage]:
        """Retrieve dead-letter messages for a queue."""
        dlq = self._queues.get(f"{queue_name}-dlq")
        if dlq is None:
            return []
        return await dlq.peek(1000)

    async def requeue_dlq(self, dlq_name: str, target: str, max_messages: int = 10) -> int:
        """Re-queue messages from a DLQ back to a target queue."""
        dlq = self._queues.get(dlq_name)
        if dlq is None:
            raise QueueError(f"DLQ '{dlq_name}' not found")

        tgt = self._queues.get(target)
        if tgt is None:
            raise QueueError(f"Target queue '{target}' not found")

        requeued = 0
        while requeued < max_messages:
            msg = await dlq.dequeue("requeue", timeout=1.0)
            if msg is None:
                break
            await tgt.enqueue(msg)
            requeued += 1

        self._log.info("queue.requeued", dlq=dlq_name, target=target, count=requeued)
        return requeued

    async def get_queue_stats(self, name: str) -> QueueStats | None:
        """Return stats for a specific queue."""
        queue = self._queues.get(name)
        if queue is None:
            return None
        return await queue.get_stats()

    async def close_all(self) -> None:
        """Close all managed queues."""
        for queue in self._queues.values():
            await queue.close()
        self._queues.clear()
        self._log.info("queue.all_closed")
