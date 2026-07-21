"""Message Queue & Async Communication - in-process message queuing with DLQ support."""

from eaip.queue.events import (
    MessageDeadLettered,
    MessageDequeued,
    MessageEnqueued,
    MessageFailed,
    QueueDepthWarning,
)
from eaip.queue.exceptions import (
    QueueClosedError,
    QueueEmptyError,
    QueueError,
    QueueFullError,
)
from eaip.queue.health import QueueHealthCheck
from eaip.queue.integration import QueueRuntimeModule
from eaip.queue.manager import QueueManager
from eaip.queue.models import QueueConfig, QueueMessage, QueueStats, QueueSubscription
from eaip.queue.provider import InMemoryQueue, MessageQueue, QueueConsumer

__all__ = [
    "InMemoryQueue",
    "MessageDeadLettered",
    "MessageDequeued",
    "MessageEnqueued",
    "MessageFailed",
    "MessageQueue",
    "QueueClosedError",
    "QueueConfig",
    "QueueConsumer",
    "QueueDepthWarning",
    "QueueEmptyError",
    "QueueError",
    "QueueFullError",
    "QueueHealthCheck",
    "QueueManager",
    "QueueMessage",
    "QueueRuntimeModule",
    "QueueStats",
    "QueueSubscription",
]
