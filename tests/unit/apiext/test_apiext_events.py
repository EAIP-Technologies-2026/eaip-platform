"""Tests for :mod:`eaip.apiext.events`."""

from __future__ import annotations

import pytest

from eaip.apiext.events import (
    CacheHit,
    CacheInvalidated,
    CacheMiss,
    CompositionExecuted,
    PolicyCreated,
    PolicyUpdated,
    RateLimitApplied,
    RateLimitExceeded,
    TransformApplied,
)
from eaip.events.event import DomainEvent


class TestCompositionExecuted:
    def test_is_domain_event(self) -> None:
        assert issubclass(CompositionExecuted, DomainEvent)

    def test_fields(self) -> None:
        evt = CompositionExecuted(
            composition_id="comp-1",
            composition_name="Test",
            endpoint_path="/api/composed",
            method="GET",
            duration_ms=42.5,
            source_count=2,
            success=True,
        )
        assert evt.composition_id == "comp-1"
        assert evt.composition_name == "Test"
        assert evt.duration_ms == 42.5
        assert evt.success is True
        assert evt.event_type == "eaip.apiext.composition.executed"

    def test_frozen(self) -> None:
        evt = CompositionExecuted(
            composition_id="c1",
            composition_name="T",
            endpoint_path="/p",
            method="GET",
            duration_ms=1.0,
            source_count=1,
            success=True,
        )
        with pytest.raises(ValueError):
            evt.success = False


class TestCacheHit:
    def test_is_domain_event(self) -> None:
        assert issubclass(CacheHit, DomainEvent)

    def test_fields(self) -> None:
        evt = CacheHit(cache_key="user:42", hit_count=5)
        assert evt.cache_key == "user:42"
        assert evt.hit_count == 5
        assert evt.event_type == "eaip.apiext.cache.hit"


class TestCacheMiss:
    def test_is_domain_event(self) -> None:
        assert issubclass(CacheMiss, DomainEvent)

    def test_fields(self) -> None:
        evt = CacheMiss(cache_key="unknown")
        assert evt.cache_key == "unknown"
        assert evt.event_type == "eaip.apiext.cache.miss"


class TestCacheInvalidated:
    def test_is_domain_event(self) -> None:
        assert issubclass(CacheInvalidated, DomainEvent)

    def test_fields(self) -> None:
        evt = CacheInvalidated(cache_key="user:42", pattern="user:*")
        assert evt.cache_key == "user:42"
        assert evt.pattern == "user:*"
        assert evt.event_type == "eaip.apiext.cache.invalidated"


class TestRateLimitApplied:
    def test_is_domain_event(self) -> None:
        assert issubclass(RateLimitApplied, DomainEvent)

    def test_fields(self) -> None:
        evt = RateLimitApplied(
            policy_id="rl-1",
            policy_name="Standard",
            key="user:42",
            max_requests=100,
            window_seconds=60.0,
            remaining=99,
            reset_at=12345.0,
        )
        assert evt.policy_id == "rl-1"
        assert evt.remaining == 99
        assert evt.event_type == "eaip.apiext.ratelimit.applied"


class TestRateLimitExceeded:
    def test_is_domain_event(self) -> None:
        assert issubclass(RateLimitExceeded, DomainEvent)

    def test_fields(self) -> None:
        evt = RateLimitExceeded(
            policy_id="rl-1",
            policy_name="Standard",
            key="user:42",
            max_requests=100,
            window_seconds=60.0,
            reset_at=12345.0,
        )
        assert evt.policy_id == "rl-1"
        assert evt.event_type == "eaip.apiext.ratelimit.exceeded"


class TestTransformApplied:
    def test_is_domain_event(self) -> None:
        assert issubclass(TransformApplied, DomainEvent)

    def test_fields(self) -> None:
        evt = TransformApplied(
            transform_id="tf-1",
            transform_name="Strip PII",
            endpoint_pattern="/api/**",
            transformation_count=3,
        )
        assert evt.transform_id == "tf-1"
        assert evt.event_type == "eaip.apiext.transform.applied"


class TestPolicyCreated:
    def test_is_domain_event(self) -> None:
        assert issubclass(PolicyCreated, DomainEvent)

    def test_fields(self) -> None:
        evt = PolicyCreated(
            policy_id="rl-1",
            policy_name="Standard",
            policy_type="rate_limit",
        )
        assert evt.policy_id == "rl-1"
        assert evt.event_type == "eaip.apiext.policy.created"


class TestPolicyUpdated:
    def test_is_domain_event(self) -> None:
        assert issubclass(PolicyUpdated, DomainEvent)

    def test_fields(self) -> None:
        evt = PolicyUpdated(
            policy_id="rl-1",
            policy_name="Standard",
            policy_type="rate_limit",
        )
        assert evt.policy_id == "rl-1"
        assert evt.event_type == "eaip.apiext.policy.updated"
