"""Message queue provider — abstract interface, in-memory implementation, consumer."""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from eaip.logging.context import get_logger
from eaip.queue.events import MessageDeadLettered, MessageDequeued, MessageEnqueued, MessageFailed
from eaip.queue.exceptions import QueueClosedError, QueueFullError
from eaip.queue.models import QueueConfig, QueueMessage, QueueStats


class MessageQueue(ABC):
    """Abstract message queue interface."""

    @abstractmethod
    async def enqueue(self, message: QueueMessage) -> None:
        """Publish a message onto the queue."""
        ...

    @abstractmethod
    async def dequeue(
        self,
        consumer_id: str,
        *,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> QueueMessage | None:
        """Retrieve the next available message."""
        ...

    @abstractmethod
    async def acknowledge(self, message_id: str) -> bool:
        """Mark a message as successfully processed."""
        ...

    @abstractmethod
    async def peek(self, count: int = 1) -> list[QueueMessage]:
        """Inspect messages without dequeuing them."""
        ...

    @abstractmethod
    async def purge(self) -> int:
        """Remove all messages. Returns the count of removed messages."""
        ...

    @abstractmethod
    async def get_stats(self) -> QueueStats:
        """Return current queue statistics."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Release resources and stop accepting messages."""
        ...


class _MessageEntry:
    """Internal wrapper that tracks visibility state."""

    __slots__ = ("dequeue_count", "message", "receive_count", "visible_after")

    def __init__(self, message: QueueMessage) -> None:
        self.message = message
        self.visible_after: datetime = datetime.now(UTC)
        self.receive_count: int = 0
        self.dequeue_count: int = 0


class InMemoryQueue(MessageQueue):
    """Thread-safe asyncio-based in-memory queue with visibility timeout and DLQ."""

    def __init__(self, config: QueueConfig, event_bus: Any = None) -> None:
        """Initialize the in-memory queue."""
        self._config = config
        self._event_bus = event_bus
        self._messages: list[_MessageEntry] = []
        self._dead_letter: list[QueueMessage] = []
        self._closed = False
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
        self._total_enqueued = 0
        self._total_dequeued = 0
        self._total_failed = 0
        self._log = get_logger("eaip.queue.in_memory")

    async def enqueue(self, message: QueueMessage) -> None:
        """Enqueue a message."""
        async with self._lock:
            if self._closed:
                raise QueueClosedError(f"Queue '{self._config.name}' is closed")
            if len(self._messages) >= self._config.max_size:
                raise QueueFullError(
                    f"Queue '{self._config.name}' is full ({self._config.max_size} messages)"
                )
            entry = _MessageEntry(message)
            if self._config.delivery_delay_seconds > 0:
                entry.visible_after = datetime.now(UTC) + timedelta(
                    seconds=self._config.delivery_delay_seconds
                )
            self._messages.append(entry)
            self._total_enqueued += 1
            self._not_empty.notify()

        if self._event_bus is not None:
            await self._event_bus.publish(
                MessageEnqueued(
                    queue_name=self._config.name,
                    message_id=message.message_id,
                    content_type=message.content_type,
                )
            )

    async def dequeue(
        self,
        consumer_id: str,
        *,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> QueueMessage | None:
        """Dequeue the next available message."""
        async with self._lock:
            deadline: datetime | None = None
            if timeout is not None:
                deadline = datetime.now(UTC) + timedelta(seconds=timeout)

            while True:
                if self._closed:
                    raise QueueClosedError(f"Queue '{self._config.name}' is closed")

                now = datetime.now(UTC)
                for entry in self._messages:
                    if entry.visible_after <= now:
                        entry.receive_count += 1
                        entry.dequeue_count += 1
                        entry.visible_after = now + timedelta(
                            seconds=self._config.visibility_timeout_seconds
                        )
                        self._total_dequeued += 1

                        if self._event_bus is not None:
                            await self._event_bus.publish(
                                MessageDequeued(
                                    queue_name=self._config.name,
                                    message_id=entry.message.message_id,
                                    consumer_id=consumer_id,
                                )
                            )
                        return entry.message

                if deadline is not None:
                    remaining = (deadline - datetime.now(UTC)).total_seconds()
                    if remaining <= 0:
                        return None
                    try:
                        await asyncio.wait_for(self._not_empty.wait(), timeout=remaining)
                    except TimeoutError:
                        return None
                else:
                    await self._not_empty.wait()

    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge a message by marking it as processed."""
        async with self._lock:
            for i, entry in enumerate(self._messages):
                if entry.message.message_id == message_id:
                    self._messages.pop(i)
                    return True
            return False

    async def peek(self, count: int = 1) -> list[QueueMessage]:
        """Peek at messages without dequeuing."""
        async with self._lock:
            if self._closed:
                raise QueueClosedError(f"Queue '{self._config.name}' is closed")
            now = datetime.now(UTC)
            visible = [e for e in self._messages if e.visible_after <= now]
            return [e.message for e in visible[:count]]

    async def purge(self) -> int:
        """Purge all messages from the queue."""
        async with self._lock:
            if self._closed:
                raise QueueClosedError(f"Queue '{self._config.name}' is closed")
            count = len(self._messages)
            self._messages.clear()
            return count

    async def get_stats(self) -> QueueStats:
        """Get current queue statistics."""
        async with self._lock:
            return QueueStats(
                total_enqueued=self._total_enqueued,
                total_dequeued=self._total_dequeued,
                total_failed=self._total_failed,
                current_depth=len(self._messages),
                dead_letter_depth=len(self._dead_letter),
            )

    async def close(self) -> None:
        """Close the queue and release resources."""
        async with self._lock:
            self._closed = True
            self._messages.clear()
            self._dead_letter.clear()
            self._not_empty.notify_all()

    async def _move_to_dead_letter(self, message: QueueMessage, reason: str) -> None:
        self._dead_letter.append(message)
        if self._event_bus is not None:
            await self._event_bus.publish(
                MessageDeadLettered(
                    queue_name=self._config.name,
                    message_id=message.message_id,
                    reason=reason,
                )
            )

    @property
    def config(self) -> QueueConfig:
        """Return the queue configuration."""
        return self._config


class QueueConsumer:
    """Message consumer with automatic acknowledge, retry, and error handling."""

    def __init__(
        self,
        queue: MessageQueue,
        handler: Callable[[QueueMessage], Any],
        *,
        consumer_id: str | None = None,
        max_retries: int = 3,
        event_bus: Any = None,
    ) -> None:
        """Initialize the queue consumer."""
        self._queue = queue
        self._handler = handler
        self._consumer_id = consumer_id or f"consumer-{uuid.uuid4().hex}"
        self._max_retries = max_retries
        self._event_bus = event_bus
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._log = get_logger("eaip.queue.consumer")

    @property
    def consumer_id(self) -> str:
        """Return the consumer identifier."""
        return self._consumer_id

    async def start(self) -> None:
        """Start consuming messages in a background task."""
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop consuming messages."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        while self._running:
            try:
                message = await self._queue.dequeue(self._consumer_id, timeout=1.0)
            except QueueClosedError:
                self._running = False
                break

            if message is None:
                continue

            try:
                result = self._handler(message)
                if asyncio.iscoroutine(result):
                    await result
                await self._queue.acknowledge(message.message_id)
            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {exc}"
                self._log.error(
                    "consumer.handler_failed",
                    consumer_id=self._consumer_id,
                    message_id=message.message_id,
                    error=error_msg,
                )

                new_retry_count = message.retry_count + 1
                will_retry = new_retry_count < self._max_retries

                if self._event_bus is not None:
                    cfg = getattr(self._queue, "config", None)
                    queue_name = cfg.name if cfg is not None else "unknown"
                    await self._event_bus.publish(
                        MessageFailed(
                            queue_name=queue_name,
                            message_id=message.message_id,
                            error=error_msg,
                            retry_count=new_retry_count,
                            will_retry=will_retry,
                        )
                    )

                if will_retry:
                    retry_msg = QueueMessage(
                        message_id=message.message_id,
                        payload=message.payload,
                        content_type=message.content_type,
                        correlation_id=message.correlation_id,
                        headers=message.headers,
                        created_at=message.created_at,
                        retry_count=new_retry_count,
                        max_retries=message.max_retries,
                    )
                    await self._queue.enqueue(retry_msg)
                elif hasattr(self._queue, "_move_to_dead_letter"):
                    await self._queue._move_to_dead_letter(message, error_msg)
