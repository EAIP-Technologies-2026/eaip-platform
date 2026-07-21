"""RateLimiter — token bucket algorithm, sliding window, per-route limits, burst support."""

from __future__ import annotations

import re
from datetime import timedelta

from eaip.logging.context import get_logger
from eaip.ratelimit.events import RateLimitExceeded, RateLimitRuleCreated, RateLimitRuleUpdated
from eaip.ratelimit.exceptions import RateLimitExceededError
from eaip.ratelimit.models import (
    RateLimitConfig,
    RateLimitResult,
    RateLimitRule,
    SlidingWindowState,
    TokenBucket,
)
from eaip.shared.time import utc_now


class RateLimiter:
    """Async rate limiter using token bucket and sliding window algorithms."""

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self._config = config or RateLimitConfig()
        self._rules: dict[str, RateLimitRule] = {}
        self._buckets: dict[str, TokenBucket] = {}
        self._windows: dict[str, SlidingWindowState] = {}
        self._log = get_logger("eaip.ratelimit.limiter")

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    async def create_rule(self, rule: RateLimitRule) -> RateLimitRule:
        """Create a new rate limit rule."""
        self._rules[rule.id] = rule
        RateLimitRuleCreated(rule_id=rule.id, route_pattern=rule.route_pattern, method=rule.method)
        self._log.info("ratelimit.rule.created", rule_id=rule.id, route=rule.route_pattern)
        return rule

    async def update_rule(self, rule_id: str, **changes: object) -> RateLimitRule:
        """Update an existing rate limit rule."""
        existing = self._rules.get(rule_id)
        if existing is None:
            raise KeyError(f"Rule not found: {rule_id}")
        updated = existing.model_copy(update=changes)
        self._rules[rule_id] = updated
        RateLimitRuleUpdated(rule_id=rule_id, changes={k: v for k, v in changes.items()})
        self._log.info("ratelimit.rule.updated", rule_id=rule_id)
        return updated

    async def get_rule(self, rule_id: str) -> RateLimitRule:
        """Get a rate limit rule by ID."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise KeyError(f"Rule not found: {rule_id}")
        return rule

    async def list_rules(self) -> list[RateLimitRule]:
        """List all registered rate limit rules."""
        return list(self._rules.values())

    async def check_request(self, key: str, path: str, method: str) -> RateLimitResult:
        """Check if a request is allowed based on matching rules and token bucket state."""
        if not self._config.enabled:
            return RateLimitResult(allowed=True, key=key, remaining=999999)

        matching_rule = await self._match_rule(path, method)
        if matching_rule is None:
            return RateLimitResult(
                allowed=True,
                key=key,
                remaining=self._config.global_max_requests,
                reset_at=utc_now() + timedelta(seconds=self._config.default_window_seconds),
            )

        result = await self._check_token_bucket(key, matching_rule)
        if not result.allowed:
            RateLimitExceeded(
                key=key,
                max_requests=matching_rule.max_requests,
                retry_after_seconds=result.retry_after_seconds,
            )
            raise RateLimitExceededError(
                f"Rate limit exceeded for key {key}",
                context={
                    "key": key,
                    "rule_id": matching_rule.id,
                    "retry_after": result.retry_after_seconds,
                },
            )

        return result

    async def _match_rule(self, path: str, method: str) -> RateLimitRule | None:
        """Find the first rule matching the given path and method."""
        for rule in self._rules.values():
            if method != "*" and rule.method != "*" and rule.method.upper() != method.upper():
                continue
            pattern = rule.route_pattern.replace("*", ".*")
            if re.fullmatch(pattern, path):
                return rule
        return None

    async def _check_token_bucket(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        """Evaluate the token bucket for a given key and rule."""
        now = utc_now()
        bucket = self._buckets.get(key)

        if bucket is None:
            capacity = rule.max_requests * rule.burst_multiplier
            bucket = TokenBucket(
                key=key,
                tokens=capacity,
                capacity=capacity,
                refill_rate=rule.max_requests / rule.window_seconds,
                last_refilled=now,
            )
            self._buckets[key] = bucket

        elapsed = (now - bucket.last_refilled).total_seconds()
        refill = elapsed * bucket.refill_rate
        new_tokens = min(bucket.tokens + refill, bucket.capacity)

        if new_tokens < 1:
            retry_after = (
                int((1 - new_tokens) / bucket.refill_rate)
                if bucket.refill_rate > 0
                else rule.window_seconds
            )
            return RateLimitResult(
                allowed=False,
                key=key,
                remaining=0,
                reset_at=now + timedelta(seconds=retry_after),
                retry_after_seconds=retry_after,
            )

        consumed = bucket.model_copy(update={"tokens": new_tokens - 1, "last_refilled": now})
        self._buckets[key] = consumed

        return RateLimitResult(
            allowed=True,
            key=key,
            remaining=int(consumed.tokens),
            reset_at=now
            + timedelta(seconds=int((consumed.capacity - consumed.tokens) / consumed.refill_rate))
            if consumed.refill_rate > 0
            else now,
        )

    async def check_sliding_window(self, key: str, rule: RateLimitRule) -> RateLimitResult:
        """Evaluate the sliding window counter for a given key and rule."""
        now = utc_now()
        window = self._windows.get(key)

        if window is None:
            window = SlidingWindowState(
                key=key, window_start=now, request_count=1, window_seconds=rule.window_seconds
            )
            self._windows[key] = window
            return RateLimitResult(
                allowed=True,
                key=key,
                remaining=rule.max_requests - 1,
                reset_at=now + timedelta(seconds=rule.window_seconds),
            )

        elapsed = (now - window.window_start).total_seconds()
        if elapsed >= rule.window_seconds:
            window = SlidingWindowState(
                key=key, window_start=now, request_count=1, window_seconds=rule.window_seconds
            )
            self._windows[key] = window
            return RateLimitResult(
                allowed=True,
                key=key,
                remaining=rule.max_requests - 1,
                reset_at=now + timedelta(seconds=rule.window_seconds),
            )

        if window.request_count >= rule.max_requests:
            retry_after = int(rule.window_seconds - elapsed)
            return RateLimitResult(
                allowed=False,
                key=key,
                remaining=0,
                reset_at=window.window_start + timedelta(seconds=rule.window_seconds),
                retry_after_seconds=retry_after,
            )

        updated = window.model_copy(update={"request_count": window.request_count + 1})
        self._windows[key] = updated
        remaining = rule.max_requests - updated.request_count
        return RateLimitResult(
            allowed=True,
            key=key,
            remaining=remaining,
            reset_at=window.window_start + timedelta(seconds=rule.window_seconds),
        )

    async def get_bucket(self, key: str) -> TokenBucket | None:
        """Get the token bucket state for a key."""
        return self._buckets.get(key)

    async def get_window(self, key: str) -> SlidingWindowState | None:
        """Get the sliding window state for a key."""
        return self._windows.get(key)


__all__ = ["RateLimiter"]
