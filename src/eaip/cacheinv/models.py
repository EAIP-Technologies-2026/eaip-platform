"""Data models for cache invalidation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CacheTag(BaseModel):
    """A cache tag used for selective invalidation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    pattern: str = Field(default="")
    ttl_seconds: int = Field(default=3600, ge=0)
    created_at: datetime = Field(default_factory=utc_now)


class InvalidationRequest(BaseModel):
    """A request to invalidate cache entries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tags: tuple[str, ...] = Field(default=())
    pattern: str = Field(default="")
    reason: str = Field(default="")
    requested_at: datetime = Field(default_factory=utc_now)


class InvalidationResult(BaseModel):
    """The result of a cache invalidation operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    invalidated_count: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)


class InvalidatorConfig(BaseModel):
    """Configuration for the cache invalidator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    batch_size: int = Field(default=100, ge=1)
    max_tags_per_request: int = Field(default=50, ge=1)
    default_ttl_seconds: int = Field(default=3600, ge=0)
    concurrency_limit: int = Field(default=10, ge=1)


__all__ = [
    "CacheTag",
    "InvalidationRequest",
    "InvalidationResult",
    "InvalidatorConfig",
]
