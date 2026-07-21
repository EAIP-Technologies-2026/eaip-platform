"""Tests for :mod:`eaip.apiext.rate_limit_policy`."""

from __future__ import annotations

import pytest

from eaip.apiext.exceptions import PolicyNotFoundError
from eaip.apiext.models import RateLimitPolicy
from eaip.apiext.rate_limit_policy import RateLimitPolicyEngine


class TestRateLimitPolicyEngine:
    @pytest.fixture
    def engine(self) -> RateLimitPolicyEngine:
        return RateLimitPolicyEngine()

    @pytest.fixture
    def sample_policy(self) -> RateLimitPolicy:
        return RateLimitPolicy(
            id="rl-std",
            name="Standard",
            key_pattern="{subject_id}",
            max_requests=100,
            window_seconds=60.0,
        )

    def test_create_policy(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        result = engine.create_policy(sample_policy)
        assert result.id == "rl-std"
        assert result == sample_policy

    def test_create_duplicate_raises(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        engine.create_policy(sample_policy)
        with pytest.raises(ValueError, match="already exists"):
            engine.create_policy(sample_policy)

    def test_get_policy(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        engine.create_policy(sample_policy)
        result = engine.get_policy("rl-std")
        assert result == sample_policy

    def test_get_policy_nonexistent(self, engine: RateLimitPolicyEngine) -> None:
        assert engine.get_policy("nonexistent") is None

    def test_update_policy(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        engine.create_policy(sample_policy)
        updated = engine.update_policy("rl-std", {"max_requests": 200})
        assert updated.max_requests == 200
        assert updated.name == "Standard"

    def test_update_nonexistent_raises(self, engine: RateLimitPolicyEngine) -> None:
        with pytest.raises(PolicyNotFoundError):
            engine.update_policy("nonexistent", {"max_requests": 50})

    def test_delete_policy(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        engine.create_policy(sample_policy)
        engine.delete_policy("rl-std")
        assert engine.get_policy("rl-std") is None

    def test_delete_nonexistent_raises(self, engine: RateLimitPolicyEngine) -> None:
        with pytest.raises(PolicyNotFoundError):
            engine.delete_policy("nonexistent")

    def test_list_policies_empty(self, engine: RateLimitPolicyEngine) -> None:
        assert engine.list_policies() == []

    def test_list_policies(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        engine.create_policy(sample_policy)
        policies = engine.list_policies()
        assert len(policies) == 1
        assert policies[0].id == "rl-std"

    async def test_check_rate_limit_allowed(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        engine.create_policy(sample_policy)
        allowed, remaining, reset_at = await engine.check_rate_limit("user:42", sample_policy)
        assert allowed is True
        assert remaining == 99
        assert reset_at > 0

    async def test_check_rate_limit_multiple_requests(self, engine: RateLimitPolicyEngine) -> None:
        policy = RateLimitPolicy(
            id="rl-low",
            name="Low",
            key_pattern="{subject_id}",
            max_requests=3,
            window_seconds=60.0,
        )
        engine.create_policy(policy)

        for _ in range(3):
            allowed, remaining, _ = await engine.check_rate_limit("user:1", policy)
            assert allowed is True

        # Fourth request should exceed the burst limit (burst = max_requests * 1.0 = 3)
        allowed, _remaining, _ = await engine.check_rate_limit("user:1", policy)
        assert allowed is False

    async def test_check_rate_limit_with_burst(self, engine: RateLimitPolicyEngine) -> None:
        policy = RateLimitPolicy(
            id="rl-burst",
            name="Bursty",
            key_pattern="{subject_id}",
            max_requests=5,
            window_seconds=60.0,
            burst_multiplier=2.0,
        )
        engine.create_policy(policy)

        for _ in range(10):
            allowed, remaining, _ = await engine.check_rate_limit("user:burst", policy)
            if not allowed:
                break

        # Should allow up to 10 (5 * 2.0) before blocking
        allowed, _remaining, _ = await engine.check_rate_limit("user:burst", policy)
        assert allowed is False

    async def test_check_rate_limit_different_keys_independent(
        self,
        engine: RateLimitPolicyEngine,
        sample_policy: RateLimitPolicy,
    ) -> None:
        engine.create_policy(sample_policy)
        # Use up limit for key1
        low_policy = RateLimitPolicy(
            id="rl-low",
            name="Low",
            key_pattern="{subject_id}",
            max_requests=1,
            window_seconds=60.0,
        )
        engine.create_policy(low_policy)

        await engine.check_rate_limit("key1", low_policy)
        allowed, _, _ = await engine.check_rate_limit("key1", low_policy)
        assert allowed is False

        allowed, _, _ = await engine.check_rate_limit("key2", low_policy)
        assert allowed is True

    def test_get_rate_limit_headers(
        self, engine: RateLimitPolicyEngine, sample_policy: RateLimitPolicy
    ) -> None:
        engine.create_policy(sample_policy)
        headers = engine.get_rate_limit_headers("user:1", sample_policy)
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers
        assert headers["X-RateLimit-Limit"] == "100"

    def test_get_rate_limit_headers_after_use(self, engine: RateLimitPolicyEngine) -> None:
        policy = RateLimitPolicy(
            id="rl-test",
            name="Test",
            key_pattern="{subject_id}",
            max_requests=10,
            window_seconds=60.0,
        )
        engine.create_policy(policy)
        # Simulate use
        import time

        from eaip.apiext.rate_limit_policy import _SlidingWindowCounter

        counter = _SlidingWindowCounter()
        counter._timestamps = [time.monotonic() - 5] * 3
        engine._counters["user:1"] = counter

        headers = engine.get_rate_limit_headers("user:1", policy)
        assert headers["X-RateLimit-Remaining"] == "7"

    async def test_policy_not_found_on_update(self, engine: RateLimitPolicyEngine) -> None:
        with pytest.raises(PolicyNotFoundError):
            engine.update_policy("ghost", {"max_requests": 10})

    async def test_policy_not_found_on_delete(self, engine: RateLimitPolicyEngine) -> None:
        with pytest.raises(PolicyNotFoundError):
            engine.delete_policy("ghost")
