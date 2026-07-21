"""Data models for rate limiting — rules, buckets, config, and results."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ThrottleRule(BaseModel):
    """A single rate limiting rule definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    max_requests: int = Field(default=0, ge=0)
    window_seconds: int = Field(default=0, ge=0)
    priority: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThrottleBucket(BaseModel):
    """A token bucket for rate limiting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    tokens: int = Field(default=0, ge=0)
    capacity: int = Field(default=0, ge=0)
    refill_rate: float = Field(default=0, ge=0)
    last_refilled: datetime = Field(default_factory=utc_now)


class ThrottleConfig(BaseModel):
    """Configuration for the rate limiting engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    global_max_requests: int = Field(default=1000, ge=0)
    default_window_seconds: int = Field(default=60, ge=0)
    header_limit: str = Field(default="X-RateLimit-Limit")
    header_remaining: str = Field(default="X-RateLimit-Remaining")


class ThrottleResult(BaseModel):
    """The result of a rate limit evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    allowed: bool
    remaining: int = Field(default=0, ge=0)
    reset_at: datetime = Field(default_factory=utc_now)
    retry_after_seconds: int = Field(default=0, ge=0)


__all__ = [
    "ThrottleBucket",
    "ThrottleConfig",
    "ThrottleResult",
    "ThrottleRule",
]
