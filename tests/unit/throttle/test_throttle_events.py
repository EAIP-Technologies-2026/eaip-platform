"""Tests for :mod:`eaip.throttle.events`."""

from __future__ import annotations

import pytest

from eaip.throttle.events import BucketRefilled, RequestThrottled, ThrottleRuleUpdated


class TestRequestThrottled:
    """Tests for :class:`eaip.throttle.events.RequestThrottled`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = RequestThrottled(rule_id="r1", consumer_id="c1", retry_after_seconds=30)
        assert e.event_type == "eaip.throttle.request.throttled"
        assert e.retry_after_seconds == 30

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = RequestThrottled(rule_id="r1", consumer_id="c1", retry_after_seconds=1)
        with pytest.raises(ValueError):
            e.retry_after_seconds = 2


class TestBucketRefilled:
    """Tests for :class:`eaip.throttle.events.BucketRefilled`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = BucketRefilled(rule_id="r1", tokens_added=50, total_tokens=100)
        assert e.event_type == "eaip.throttle.bucket.refilled"
        assert e.tokens_added == 50


class TestThrottleRuleUpdated:
    """Tests for :class:`eaip.throttle.events.ThrottleRuleUpdated`."""

    def test_create(self) -> None:
        """Test creating an event with required fields."""
        e = ThrottleRuleUpdated(rule_id="r1", changes={"max_requests": 200})
        assert e.event_type == "eaip.throttle.rule.updated"
        assert e.changes["max_requests"] == 200


def test_all_events_have_unique_types() -> None:
    """Test that all event types are unique."""
    types = [
        RequestThrottled(rule_id="r1", consumer_id="c1", retry_after_seconds=1).event_type,
        BucketRefilled(rule_id="r1", tokens_added=1, total_tokens=1).event_type,
        ThrottleRuleUpdated(rule_id="r1").event_type,
    ]
    assert len(types) == len(set(types))
