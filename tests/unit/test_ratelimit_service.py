"""Tests for RateLimiter."""

from __future__ import annotations

import pytest

from eaip.ratelimit.exceptions import RateLimitExceededError
from eaip.ratelimit.limiter import RateLimiter
from eaip.ratelimit.models import RateLimitConfig, RateLimitRule


class TestRateLimiter:
    @pytest.fixture
    def limiter(self) -> RateLimiter:
        return RateLimiter()

    @pytest.fixture
    def sample_rule(self) -> RateLimitRule:
        return RateLimitRule(
            id="r1",
            route_pattern="/api/*",
            method="GET",
            max_requests=5,
            window_seconds=10,
            burst_multiplier=2.0,
        )

    class TestCreateRule:
        async def test_creates_rule(self, limiter: RateLimiter, sample_rule: RateLimitRule) -> None:
            result = await limiter.create_rule(sample_rule)
            assert result.id == "r1"
            assert result.route_pattern == "/api/*"

        async def test_stores_rule(self, limiter: RateLimiter, sample_rule: RateLimitRule) -> None:
            await limiter.create_rule(sample_rule)
            stored = await limiter.get_rule("r1")
            assert stored.id == "r1"

    class TestGetRule:
        async def test_returns_rule(self, limiter: RateLimiter, sample_rule: RateLimitRule) -> None:
            await limiter.create_rule(sample_rule)
            result = await limiter.get_rule("r1")
            assert result.max_requests == 5

        async def test_raises_on_missing(self, limiter: RateLimiter) -> None:
            with pytest.raises(KeyError):
                await limiter.get_rule("nonexistent")

    class TestUpdateRule:
        async def test_updates_rule(self, limiter: RateLimiter, sample_rule: RateLimitRule) -> None:
            await limiter.create_rule(sample_rule)
            updated = await limiter.update_rule("r1", max_requests=10)
            assert updated.max_requests == 10

        async def test_raises_on_missing(self, limiter: RateLimiter) -> None:
            with pytest.raises(KeyError):
                await limiter.update_rule("nonexistent", max_requests=5)

    class TestListRules:
        async def test_empty_when_none(self, limiter: RateLimiter) -> None:
            assert await limiter.list_rules() == []

        async def test_returns_all(self, limiter: RateLimiter, sample_rule: RateLimitRule) -> None:
            await limiter.create_rule(sample_rule)
            rules = await limiter.list_rules()
            assert len(rules) == 1

    class TestCheckRequest:
        async def test_allows_within_limit(
            self, limiter: RateLimiter, sample_rule: RateLimitRule
        ) -> None:
            await limiter.create_rule(sample_rule)
            result = await limiter.check_request("key1", "/api/test", "GET")
            assert result.allowed is True
            assert result.remaining >= 0

        async def test_raises_when_exceeded(self, limiter: RateLimiter) -> None:
            rule = RateLimitRule(
                id="r2", route_pattern="/*", method="*", max_requests=1, window_seconds=60
            )
            await limiter.create_rule(rule)
            await limiter.check_request("key2", "/test", "GET")
            with pytest.raises(RateLimitExceededError):
                await limiter.check_request("key2", "/test", "GET")

        async def test_allows_when_disabled(self, limiter: RateLimiter) -> None:
            cfg = RateLimitConfig(enabled=False)
            disabled = RateLimiter(config=cfg)
            result = await disabled.check_request("key", "/test", "GET")
            assert result.allowed is True

    class TestCheckSlidingWindow:
        async def test_allows_within_window(self, limiter: RateLimiter) -> None:
            rule = RateLimitRule(
                id="r3", route_pattern="/*", method="*", max_requests=5, window_seconds=60
            )
            await limiter.create_rule(rule)
            result = await limiter.check_sliding_window("key3", rule)
            assert result.allowed is True

        async def test_blocks_when_exceeded(self, limiter: RateLimiter) -> None:
            rule = RateLimitRule(
                id="r4", route_pattern="/*", method="*", max_requests=1, window_seconds=60
            )
            await limiter.create_rule(rule)
            await limiter.check_sliding_window("key4", rule)
            result = await limiter.check_sliding_window("key4", rule)
            assert result.allowed is False

    class TestGetBucket:
        async def test_returns_none_for_new_key(self, limiter: RateLimiter) -> None:
            assert await limiter.get_bucket("nonexistent") is None

        async def test_returns_bucket_after_check(
            self, limiter: RateLimiter, sample_rule: RateLimitRule
        ) -> None:
            await limiter.create_rule(sample_rule)
            await limiter.check_request("key5", "/api/test", "GET")
            bucket = await limiter.get_bucket("key5")
            assert bucket is not None
            assert bucket.key == "key5"

    class TestGetWindow:
        async def test_returns_none_for_new_key(self, limiter: RateLimiter) -> None:
            assert await limiter.get_window("nonexistent") is None

        async def test_returns_window_after_check(self, limiter: RateLimiter) -> None:
            rule = RateLimitRule(
                id="r5", route_pattern="/*", method="*", max_requests=5, window_seconds=60
            )
            await limiter.create_rule(rule)
            await limiter.check_sliding_window("key6", rule)
            window = await limiter.get_window("key6")
            assert window is not None
            assert window.key == "key6"

    class TestConfig:
        def test_default_config(self) -> None:
            limiter = RateLimiter()
            assert limiter.config.global_max_requests == 1000

        def test_custom_config(self) -> None:
            cfg = RateLimitConfig(global_max_requests=500)
            limiter = RateLimiter(config=cfg)
            assert limiter.config.global_max_requests == 500
