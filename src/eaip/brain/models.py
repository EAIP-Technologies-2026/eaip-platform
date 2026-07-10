"""Enterprise Brain models — queries, results, sources, and configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BrainSource(BaseModel):
    """A single result source returned by the Enterprise Brain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_type: str
    source_id: str
    content_preview: str
    relevance_score: float = 0.0
    collection: str = ""


class BrainQuery(BaseModel):
    """A query against the Enterprise Brain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    top_k: int = 10
    score_threshold: float = 0.0
    include_knowledge: bool = True
    include_memory: bool = True
    include_context: bool = True
    filters: dict[str, Any] = Field(default_factory=dict)
    max_tokens: int = 4096
    collection_names: tuple[str, ...] = ()


class BrainResult(BaseModel):
    """The aggregated result from an Enterprise Brain query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    answer: str = ""
    confidence: float = 0.0
    sources: tuple[BrainSource, ...] = ()
    duration_ms: float = 0.0
    token_count: int = 0


class EnterpriseBrainConfig(BaseModel):
    """Configuration for the Enterprise Brain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_top_k: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    max_tokens_per_source: int = 2000
    enable_reranking: bool = True


__all__ = [
    "BrainQuery",
    "BrainResult",
    "BrainSource",
    "EnterpriseBrainConfig",
]
