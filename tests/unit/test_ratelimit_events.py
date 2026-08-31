"""Tests for rate limit domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.ratelimit.events import RateLimitExceeded, RateLimitRuleCreated, RateLimitRuleUpdated


class TestRateLimitExceeded:
    def test_defaults(self) -> None:
        e = RateLimitExceeded(key="k1", max_requests=100, retry_after_seconds=30)
        assert e.event_type == "eaip.ratelimit.limit.exceeded"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = RateLimitExceeded(key="k1", max_requests=100, retry_after_seconds=30)
        assert e.key == "k1"
        assert e.max_requests == 100
        assert e.retry_after_seconds == 30

    def test_frozen(self) -> None:
        e = RateLimitExceeded(key="k1", max_requests=100, retry_after_seconds=30)
        with pytest.raises((ValueError, TypeError)):
            e.key = "k2"  # type: ignore[misc]


class TestRateLimitRuleCreated:
    def test_defaults(self) -> None:
        e = RateLimitRuleCreated(rule_id="r1", route_pattern="/api/*", method="GET")
        assert e.event_type == "eaip.ratelimit.rule.created"

    def test_with_values(self) -> None:
        e = RateLimitRuleCreated(rule_id="r1", route_pattern="/api/*", method="GET")
        assert e.rule_id == "r1"
        assert e.route_pattern == "/api/*"


class TestRateLimitRuleUpdated:
    def test_defaults(self) -> None:
        e = RateLimitRuleUpdated(rule_id="r1")
        assert e.event_type == "eaip.ratelimit.rule.updated"
        assert e.changes == {}

    def test_with_values(self) -> None:
        e = RateLimitRuleUpdated(rule_id="r1", changes={"max_requests": 50})
        assert e.changes == {"max_requests": 50}


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [RateLimitExceeded, RateLimitRuleCreated, RateLimitRuleUpdated]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
