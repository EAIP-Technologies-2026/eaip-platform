"""Pydantic models for cache entries, configuration, and statistics."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CacheEntry(BaseModel):
    """A single entry stored in the cache."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    value: bytes
    ttl_seconds: int | None = None
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    hits: int = 0
    size_bytes: int = 0


class CacheConfig(BaseModel):
    """Configuration settings for a cache instance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_ttl_seconds: int = 300
    max_size_bytes: int = 0
    max_entries: int = 10000
    namespace: str = "default"
    enable_stats: bool = False


class CacheStats(BaseModel):
    """Snapshot of cache performance and resource usage statistics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_entries: int = 0
    total_hits: int = 0
    total_misses: int = 0
    total_evictions: int = 0
    hit_ratio: float = 0.0
    size_bytes: int = 0
