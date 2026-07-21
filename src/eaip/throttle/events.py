"""Domain events for rate limiting."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class RequestThrottled(DomainEvent):
    """Emitted when a request is throttled."""

    event_type: ClassVar[str] = "eaip.throttle.request.throttled"

    rule_id: str
    consumer_id: str
    retry_after_seconds: int


class BucketRefilled(DomainEvent):
    """Emitted when a token bucket is refilled."""

    event_type: ClassVar[str] = "eaip.throttle.bucket.refilled"

    rule_id: str
    tokens_added: int
    total_tokens: int


class ThrottleRuleUpdated(DomainEvent):
    """Emitted when a throttle rule is updated."""

    event_type: ClassVar[str] = "eaip.throttle.rule.updated"

    rule_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "BucketRefilled",
    "RequestThrottled",
    "ThrottleRuleUpdated",
]
