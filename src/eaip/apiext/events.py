"""Domain events emitted by the API Extensions subsystem."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class CompositionExecuted(DomainEvent):
    """Published after a composition is executed."""

    event_type: ClassVar[str] = "eaip.apiext.composition.executed"

    composition_id: str
    composition_name: str
    endpoint_path: str
    method: str
    duration_ms: float
    source_count: int
    success: bool


class CacheHit(DomainEvent):
    """Published when a cache lookup returns a valid entry."""

    event_type: ClassVar[str] = "eaip.apiext.cache.hit"

    cache_key: str
    hit_count: int


class CacheMiss(DomainEvent):
    """Published when a cache lookup returns no entry."""

    event_type: ClassVar[str] = "eaip.apiext.cache.miss"

    cache_key: str


class CacheInvalidated(DomainEvent):
    """Published when cache entries are invalidated."""

    event_type: ClassVar[str] = "eaip.apiext.cache.invalidated"

    cache_key: str
    pattern: str


class RateLimitApplied(DomainEvent):
    """Published when a rate-limit policy is applied to a request."""

    event_type: ClassVar[str] = "eaip.apiext.ratelimit.applied"

    policy_id: str
    policy_name: str
    key: str
    max_requests: int
    window_seconds: float
    remaining: int
    reset_at: float


class RateLimitExceeded(DomainEvent):
    """Published when a rate-limit policy is exceeded."""

    event_type: ClassVar[str] = "eaip.apiext.ratelimit.exceeded"

    policy_id: str
    policy_name: str
    key: str
    max_requests: int
    window_seconds: float
    reset_at: float


class TransformApplied(DomainEvent):
    """Published after a response transformation is applied."""

    event_type: ClassVar[str] = "eaip.apiext.transform.applied"

    transform_id: str
    transform_name: str
    endpoint_pattern: str
    transformation_count: int


class PolicyCreated(DomainEvent):
    """Published when a new policy (rate-limit, transform, etc.) is created."""

    event_type: ClassVar[str] = "eaip.apiext.policy.created"

    policy_id: str
    policy_name: str
    policy_type: str


class PolicyUpdated(DomainEvent):
    """Published when an existing policy is updated."""

    event_type: ClassVar[str] = "eaip.apiext.policy.updated"

    policy_id: str
    policy_name: str
    policy_type: str


__all__ = [
    "CacheHit",
    "CacheInvalidated",
    "CacheMiss",
    "CompositionExecuted",
    "PolicyCreated",
    "PolicyUpdated",
    "RateLimitApplied",
    "RateLimitExceeded",
    "TransformApplied",
]
