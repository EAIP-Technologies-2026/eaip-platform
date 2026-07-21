"""Data models for the API Extensions subsystem."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class MergeStrategy(StrEnum):
    """Strategies for merging responses from composed endpoints."""

    CONCAT = "concat"
    MERGE = "merge"
    ZIP = "zip"
    CHAIN = "chain"


class ApiComposition(BaseModel):
    """Defines a composed API endpoint that aggregates multiple source endpoints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique composition identifier.")
    name: str = Field(description="Human-readable composition name.")
    endpoint_path: str = Field(description="The composed endpoint path.")
    method: str = Field(description="HTTP method for the composed endpoint.")
    source_endpoints: tuple[str, ...] = Field(
        description="Source endpoint paths to aggregate.",
    )
    merge_strategy: MergeStrategy = Field(
        default=MergeStrategy.CONCAT,
        description="Strategy used to merge source responses.",
    )
    response_mapping: dict[str, Any] = Field(
        default_factory=dict,
        description="Field mapping from source to composed response.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="Per-source request timeout.",
    )
    cache_ttl_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Optional cache TTL for the composed response.",
    )
    enabled: bool = Field(default=True, description="Whether this composition is active.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata attached to the composition.",
    )


class CachedResponse(BaseModel):
    """A cached API response entry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique cache entry identifier.")
    cache_key: str = Field(description="Cache key used for lookup.")
    response_body: dict[str, Any] = Field(
        default_factory=dict,
        description="Cached response body.",
    )
    status_code: int = Field(default=200, description="Cached HTTP status code.")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Cached response headers.",
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="When the entry was created.",
    )
    expires_at: datetime = Field(description="When the entry expires.")
    hit_count: int = Field(
        default=0,
        ge=0,
        description="Number of times this entry has been served.",
    )


class RateLimitPolicy(BaseModel):
    """Defines a rate-limit policy with sliding-window and burst support."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique policy identifier.")
    name: str = Field(description="Human-readable policy name.")
    key_pattern: str = Field(
        description="Pattern for the rate-limit key (e.g. '{subject_id}:{path}').",
    )
    max_requests: int = Field(gt=0, description="Maximum requests in the window.")
    window_seconds: float = Field(gt=0, description="Sliding window duration.")
    burst_multiplier: float = Field(
        default=1.0,
        ge=1.0,
        description="Multiplier for short burst allowances.",
    )
    response_headers: tuple[str, ...] = Field(
        default=("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"),
        description="Rate-limit headers to include in responses.",
    )
    status_code: int = Field(
        default=429,
        description="HTTP status code when limit is exceeded.",
    )
    error_message: str = Field(
        default="Rate limit exceeded. Please retry later.",
        description="Error message when limit is exceeded.",
    )


class ResponseTransform(BaseModel):
    """Defines a response transformation rule applied to matching endpoints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique transform identifier.")
    name: str = Field(description="Human-readable transform name.")
    endpoint_pattern: str = Field(
        description="Glob pattern matching endpoint paths.",
    )
    transformations: tuple[str, ...] = Field(
        description="Transformation operations to apply.",
    )
    enabled: bool = Field(default=True, description="Whether this transform is active.")
    priority: int = Field(
        default=0,
        description="Execution priority (higher runs first).",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata attached to the transform.",
    )


class ApiCompositionConfig(BaseModel):
    """Global configuration for the API composition subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_requests: int = Field(
        default=10,
        gt=0,
        description="Maximum concurrent source requests per composition.",
    )
    default_timeout: float = Field(
        default=30.0,
        gt=0,
        description="Default timeout for source requests.",
    )
    enable_caching: bool = Field(
        default=True,
        description="Whether composition caching is enabled.",
    )
    cache_max_size: int = Field(
        default=1000,
        gt=0,
        description="Maximum number of cached responses.",
    )
    enable_circuit_breaker: bool = Field(
        default=False,
        description="Whether circuit breaker is enabled for sources.",
    )


__all__ = [
    "ApiComposition",
    "ApiCompositionConfig",
    "CachedResponse",
    "MergeStrategy",
    "RateLimitPolicy",
    "ResponseTransform",
]
