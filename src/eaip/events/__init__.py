"""In-process event bus with sync & async subscribers, dispatcher, and lifecycle hooks."""

from __future__ import annotations

from eaip.events.bus import EventBus, Subscription
from eaip.events.dispatcher import DispatchResult, EventDispatcher
from eaip.events.envelope import EventEnvelope
from eaip.events.errors import (
    EventError,
    EventHandlerError,
    EventPublishError,
    EventRetryExhaustedError,
)
from eaip.events.event import DomainEvent
from eaip.events.hooks import EventHooks
from eaip.events.retry import (
    ExponentialBackoffRetry,
    FixedDelayRetry,
    ImmediateRetry,
    RetryStrategy,
)

__all__ = [
    "DispatchResult",
    "DomainEvent",
    "EventBus",
    "EventDispatcher",
    "EventEnvelope",
    "EventError",
    "EventHandlerError",
    "EventHooks",
    "EventPublishError",
    "EventRetryExhaustedError",
    "ExponentialBackoffRetry",
    "FixedDelayRetry",
    "ImmediateRetry",
    "RetryStrategy",
    "Subscription",
]
