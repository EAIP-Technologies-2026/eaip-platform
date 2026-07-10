"""Search models — queries, results, filters, configurations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchFilter(BaseModel):
    """A single filter criterion for a search query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "in", "contains"]
    value: Any


class Pagination(BaseModel):
    """Pagination parameters for search requests."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    page: int = Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = Field(default=20, ge=1, le=1000, description="Results per page.")
    max_page_size: int = Field(default=1000, description="Maximum allowed page size.")


class SearchQuery(BaseModel):
    """A query against the enterprise search system."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str = Field(default="", description="Search query text.")
    filters: tuple[SearchFilter, ...] = Field(default_factory=tuple)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=1000)
    sort_by: str | None = Field(default=None)
    sort_order: Literal["asc", "desc"] = Field(default="desc")
    collections: tuple[str, ...] = Field(default_factory=tuple)
    search_type: Literal["hybrid", "semantic", "keyword"] = Field(default="hybrid")
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    min_score: float = Field(default=0.0, ge=0.0)


class SearchResultItem(BaseModel):
    """A single item returned from a search query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    collection: str
    content: str
    score: float = 0.0
    title: str = ""
    source: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    highlights: dict[str, str] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Complete result from a search query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[SearchResultItem, ...] = Field(default_factory=tuple)
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    duration_ms: float = 0.0
    query: str = ""


class SearchProviderConfig(BaseModel):
    """Configuration for a search provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_type: str
    endpoint: str = ""
    api_key: str = ""
    timeout_seconds: int = 60
    max_retries: int = 3
    options: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Pagination",
    "SearchFilter",
    "SearchProviderConfig",
    "SearchQuery",
    "SearchResult",
    "SearchResultItem",
]
