"""Tests for :mod:`eaip.gateway.rate_limiter`."""

from __future__ import annotations

import time

from eaip.gateway.models import RateLimitConfig
from eaip.gateway.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_allows_within_limit(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=5, window_seconds=60.0)
        for _ in range(5):
            assert limiter.check_limit("key1", config) is True

    def test_blocks_when_exceeded(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=3, window_seconds=60.0)
        for _ in range(3):
            assert limiter.check_limit("key1", config) is True
        assert limiter.check_limit("key1", config) is False

    def test_different_keys_independent(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=1, window_seconds=60.0)
        assert limiter.check_limit("alice", config) is True
        assert limiter.check_limit("alice", config) is False
        assert limiter.check_limit("bob", config) is True

    def test_window_slides(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=2, window_seconds=0.2)

        assert limiter.check_limit("key1", config) is True
        assert limiter.check_limit("key1", config) is True
        assert limiter.check_limit("key1", config) is False

        time.sleep(0.25)
        assert limiter.check_limit("key1", config) is True

    def test_reset_single_key(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=1, window_seconds=60.0)
        assert limiter.check_limit("key1", config) is True
        assert limiter.check_limit("key1", config) is False
        limiter.reset("key1")
        assert limiter.check_limit("key1", config) is True

    def test_reset_all_keys(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=1, window_seconds=60.0)
        assert limiter.check_limit("a", config) is True
        assert limiter.check_limit("b", config) is True
        assert limiter.check_limit("a", config) is False
        limiter.reset()
        assert limiter.check_limit("a", config) is True
        assert limiter.check_limit("b", config) is True

    def test_high_volume(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=1000, window_seconds=60.0)
        for i in range(1000):
            assert limiter.check_limit(f"user{i}", config) is True

    def test_zero_window_blocks_immediately(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=1, window_seconds=1.0)
        assert limiter.check_limit("key1", config) is True
        assert limiter.check_limit("key1", config) is False
