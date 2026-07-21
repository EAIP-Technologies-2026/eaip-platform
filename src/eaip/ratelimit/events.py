"""Domain events for rate limiting."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class RateLimitExceeded(DomainEvent):
    """Emitted when a rate limit is exceeded for a given key."""

    event_type: ClassVar[str] = "eaip.ratelimit.limit.exceeded"

    key: str
    max_requests: int
    retry_after_seconds: int


class RateLimitRuleCreated(DomainEvent):
    """Emitted when a new rate limit rule is created."""

    event_type: ClassVar[str] = "eaip.ratelimit.rule.created"

    rule_id: str
    route_pattern: str
    method: str


class RateLimitRuleUpdated(DomainEvent):
    """Emitted when an existing rate limit rule is updated."""

    event_type: ClassVar[str] = "eaip.ratelimit.rule.updated"

    rule_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "RateLimitExceeded",
    "RateLimitRuleCreated",
    "RateLimitRuleUpdated",
]
