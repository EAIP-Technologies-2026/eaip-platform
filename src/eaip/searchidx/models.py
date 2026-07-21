"""Search index models — indices, fields, jobs, cache policies."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IndexField(BaseModel):
    """A field definition within a search index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: Literal["text", "keyword", "integer", "float", "date", "boolean"]
    searchable: bool = Field(default=True)
    filterable: bool = Field(default=False)
    sortable: bool = Field(default=False)
    boost: float = Field(default=1.0, ge=0.0)
    analyzer: str = Field(default="standard")


class SearchIndex(BaseModel):
    """A search index definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_type: str
    fields: tuple[IndexField, ...] = Field(default_factory=tuple)
    status: Literal["building", "ready", "failed"] = Field(default="building")
    document_count: int = Field(default=0, ge=0)
    last_built_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexJob(BaseModel):
    """A job that builds or updates a search index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    index_id: str
    type: Literal["full", "incremental"]
    status: Literal["pending", "running", "completed", "failed"] = Field(default="pending")
    documents_processed: int = Field(default=0, ge=0)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CachePolicy(BaseModel):
    """A caching policy for a key pattern."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    key_pattern: str
    ttl_seconds: int = Field(default=300, ge=1, le=86400)
    warm_on_start: bool = Field(default=False)
    invalidation_events: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchCacheConfig(BaseModel):
    """Configuration for the search cache subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_cache: bool = Field(default=True)
    default_ttl_seconds: int = Field(default=300, ge=1, le=86400)
    max_cache_size: int = Field(default=10000, ge=1, le=10000000)
    enable_warming: bool = Field(default=True)
    warming_interval_seconds: int = Field(default=60, ge=10, le=3600)


__all__ = [
    "CachePolicy",
    "IndexField",
    "IndexJob",
    "SearchCacheConfig",
    "SearchIndex",
]
