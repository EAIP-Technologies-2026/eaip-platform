"""Tests for :mod:`eaip.throttle.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.throttle.models import ThrottleBucket, ThrottleConfig, ThrottleResult, ThrottleRule


class TestThrottleRule:
    """Tests for :class:`eaip.throttle.models.ThrottleRule`."""

    def test_create_minimal(self) -> None:
        """Test creating a rule with required fields."""
        r = ThrottleRule(id="r1", name="Rate Limit", max_requests=100, window_seconds=60)
        assert r.id == "r1"
        assert r.priority == 0

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        r = ThrottleRule(id="r1", name="Test", max_requests=10, window_seconds=60)
        with pytest.raises(ValidationError):
            r.max_requests = 20


class TestThrottleBucket:
    """Tests for :class:`eaip.throttle.models.ThrottleBucket`."""

    def test_create(self) -> None:
        """Test creating a bucket with required fields."""
        b = ThrottleBucket(rule_id="r1", tokens=100, capacity=100, refill_rate=10.0)
        assert b.tokens == 100
        assert b.refill_rate == 10.0

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        b = ThrottleBucket(rule_id="r1", tokens=0, capacity=100, refill_rate=1)
        with pytest.raises(ValidationError):
            b.tokens = 50


class TestThrottleConfig:
    """Tests for :class:`eaip.throttle.models.ThrottleConfig`."""

    def test_defaults(self) -> None:
        """Test default configuration values."""
        c = ThrottleConfig()
        assert c.enabled is True
        assert c.global_max_requests == 1000
        assert c.default_window_seconds == 60

    def test_custom(self) -> None:
        """Test creating a config with custom values."""
        c = ThrottleConfig(
            enabled=False,
            global_max_requests=500,
            default_window_seconds=30,
        )
        assert c.enabled is False
        assert c.global_max_requests == 500

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        c = ThrottleConfig()
        with pytest.raises(ValidationError):
            c.enabled = False


class TestThrottleResult:
    """Tests for :class:`eaip.throttle.models.ThrottleResult`."""

    def test_create(self) -> None:
        """Test creating a result with allowed status."""
        r = ThrottleResult(rule_id="r1", allowed=True, remaining=50)
        assert r.allowed is True
        assert r.retry_after_seconds == 0

    def test_denied(self) -> None:
        """Test creating a result with denied status."""
        r = ThrottleResult(rule_id="r1", allowed=False, remaining=0, retry_after_seconds=30)
        assert r.allowed is False
        assert r.retry_after_seconds == 30

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        r = ThrottleResult(rule_id="r1", allowed=True, remaining=10)
        with pytest.raises(ValidationError):
            r.allowed = False


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        ThrottleRule(id="r1", name="Test", max_requests=10, window_seconds=60, unknown="val")
