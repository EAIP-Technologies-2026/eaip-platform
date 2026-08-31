"""Context & Prompt Intelligence models — templates, versions, context documents."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CompressionStrategy(StrEnum):
    """Strategies for compressing assembled context."""

    EXTRACTIVE = "extractive"
    SUMMARIZE = "summarize"
    TRUNCATE = "truncate"


class PromptTemplate(BaseModel):
    """A reusable prompt template with named variables and metadata.

    Variables are referenced as ``{variable_name}`` inside the template
    content and are substituted at render time.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    template_id: str
    name: str
    description: str = ""
    content: str
    variables: tuple[str, ...] = ()
    version: str = "1.0.0"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PromptVersion(BaseModel):
    """A specific version of a prompt with content, change log, and author."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    content: str
    change_log: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptRegistryEntry(BaseModel):
    """A registry entry tracking a prompt and all its versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_id: str
    current_version: str = "1.0.0"
    versions: tuple[PromptVersion, ...] = ()
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextBuilderConfig(BaseModel):
    """Configuration for context assembly behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_tokens: int = 4096
    relevance_threshold: float = 0.0
    include_sources: bool = True
    deduplicate: bool = True
    max_documents: int = 50


class ContextDocument(BaseModel):
    """A single document within an assembled context."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    content: str
    source: str = ""
    relevance_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssembledContext(BaseModel):
    """A collection of context documents with total token accounting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    documents: tuple[ContextDocument, ...] = ()
    total_tokens: int = 0
    document_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextCacheConfig(BaseModel):
    """Configuration for context caching behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ttl_seconds: int = 300
    max_entries: int = 100


class CompressionConfig(BaseModel):
    """Configuration for context compression."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE
    ratio: float = 0.5
    max_tokens: int = 2048


__all__ = [
    "AssembledContext",
    "CompressionConfig",
    "CompressionStrategy",
    "ContextBuilderConfig",
    "ContextCacheConfig",
    "ContextDocument",
    "PromptRegistryEntry",
    "PromptTemplate",
    "PromptVersion",
]
