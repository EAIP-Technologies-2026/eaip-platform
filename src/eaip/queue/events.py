"""Domain events emitted by the queue subsystem."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class MessageEnqueued(DomainEvent):
    """Emitted when a message is successfully enqueued."""

    event_type: ClassVar[str] = "eaip.queue.message_enqueued"

    queue_name: str
    message_id: str
    content_type: str


class MessageDequeued(DomainEvent):
    """Emitted when a message is dequeued by a consumer."""

    event_type: ClassVar[str] = "eaip.queue.message_dequeued"

    queue_name: str
    message_id: str
    consumer_id: str


class MessageFailed(DomainEvent):
    """Emitted when message processing fails."""

    event_type: ClassVar[str] = "eaip.queue.message_failed"

    queue_name: str
    message_id: str
    error: str
    retry_count: int
    will_retry: bool


class MessageDeadLettered(DomainEvent):
    """Emitted when a message is moved to the dead-letter queue."""

    event_type: ClassVar[str] = "eaip.queue.message_dead_lettered"

    queue_name: str
    message_id: str
    reason: str


class QueueDepthWarning(DomainEvent):
    """Emitted when queue depth exceeds a threshold."""

    event_type: ClassVar[str] = "eaip.queue.depth_warning"

    queue_name: str
    depth: int
    threshold: int
