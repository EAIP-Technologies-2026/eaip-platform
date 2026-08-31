"""Data models for rate limiting — limits, rules, config, and buckets."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RateLimit(BaseModel):
    """A current rate limit state for a given key."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    max_requests: int = Field(default=0, ge=0)
    window_seconds: int = Field(default=0, ge=0)
    current_count: int = Field(default=0, ge=0)
    reset_at: datetime = Field(default_factory=utc_now)


class RateLimitRule(BaseModel):
    """A rate limit rule tied to a route pattern and HTTP method."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    route_pattern: str
    method: str = Field(default="*")
    max_requests: int = Field(default=100, ge=0)
    window_seconds: int = Field(default=60, ge=0)
    burst_multiplier: float = Field(default=1.0, ge=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RateLimitConfig(BaseModel):
    """Configuration for the rate limiter engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    global_max_requests: int = Field(default=1000, ge=0)
    default_window_seconds: int = Field(default=60, ge=0)
    default_burst_multiplier: float = Field(default=1.5, ge=1.0)
    cleanup_interval_seconds: int = Field(default=300, ge=0)


class TokenBucket(BaseModel):
    """A token bucket state for the token-bucket algorithm."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    tokens: float = Field(default=0, ge=0)
    capacity: float = Field(default=0, ge=0)
    refill_rate: float = Field(default=0, ge=0)
    last_refilled: datetime = Field(default_factory=utc_now)


class SlidingWindowState(BaseModel):
    """A sliding window state for window-based rate limiting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    window_start: datetime = Field(default_factory=utc_now)
    request_count: int = Field(default=0, ge=0)
    window_seconds: int = Field(default=60, ge=0)


class RateLimitResult(BaseModel):
    """The result of a rate limit check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allowed: bool
    key: str
    remaining: int = Field(default=0, ge=0)
    reset_at: datetime = Field(default_factory=utc_now)
    retry_after_seconds: int = Field(default=0, ge=0)


__all__ = [
    "RateLimit",
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimitRule",
    "SlidingWindowState",
    "TokenBucket",
]
