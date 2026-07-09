"""Memory Engine models — memory items, queries, results, configurations."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class MemoryType(StrEnum):
    """Types of memory in the memory system.

    Each type serves a different purpose in the agent cognitive architecture.
    """

    WORKING = "working"
    """Short-term memory for current task context."""

    SESSION = "session"
    """Conversation or interaction session memory."""

    LONG_TERM = "long_term"
    """Persistent memory that survives across sessions."""

    EPISODIC = "episodic"
    """Memory of specific events, experiences, or interactions."""

    SEMANTIC = "semantic"
    """Factual knowledge extracted and generalized from experiences."""


class MemoryStatus(StrEnum):
    """Lifecycle status of a memory item."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    CONSOLIDATED = "consolidated"


class MemoryScope(BaseModel):
    """Scope identifier for a memory item.

    Memories are scoped to provide tenant isolation, user boundaries,
    and session context.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    user_id: str | None = None
    session_id: str | None = None
    application_id: str | None = None

    def scope_key(self) -> str:
        """Return a composite scope key for storage indexing.

        Returns:
            A colon-delimited scope string.
        """
        parts = [self.tenant_id]
        if self.user_id:
            parts.append(self.user_id)
        if self.session_id:
            parts.append(self.session_id)
        if self.application_id:
            parts.append(self.application_id)
        return ":".join(parts)


class ScopedMemoryId(BaseModel):
    """Globally unique identifier for a memory item within its scope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    memory_id: str
    scope: MemoryScope

    def fully_qualified(self) -> str:
        """Return a fully qualified memory identifier.

        Returns:
            A globally unique identifier string.
        """
        return f"{self.scope.scope_key()}:{self.memory_id}"


class MemoryItem(BaseModel):
    """A single memory item stored in the memory system."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    memory_id: str
    memory_type: MemoryType
    scope: MemoryScope
    content: str
    content_summary: str = ""
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    status: MemoryStatus = MemoryStatus.ACTIVE
    parent_id: str | None = None
    related_ids: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: tuple[float, ...] = ()
    version: int = 1
    access_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    accessed_at: datetime | None = None
    expires_at: datetime | None = None


class MemoryRelation(BaseModel):
    """A relationship between two memory items."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class MemoryQuery(BaseModel):
    """A query to retrieve memories."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str = ""
    memory_types: tuple[MemoryType, ...] = ()
    scopes: tuple[MemoryScope, ...] = ()
    tags: tuple[str, ...] = ()
    status: MemoryStatus | None = None
    importance_min: float = 0.0
    importance_max: float = 1.0
    top_k: int = 10
    score_threshold: float = 0.0
    include_embeddings: bool = False
    include_relations: bool = False
    offset: int = 0
    limit: int = 100


class MemorySearchResult(BaseModel):
    """A single memory result from a search or query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    memory: MemoryItem
    score: float = 0.0
    relations: tuple[MemoryRelation, ...] = ()


class MemoryResult(BaseModel):
    """Collection of results from a memory query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    results: tuple[MemorySearchResult, ...] = ()
    total_count: int = 0
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=utc_now)


class MemoryConfig(BaseModel):
    """Configuration for the Memory Engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_importance: float = 0.5
    max_working_memories: int = 50
    max_session_memories: int = 200
    enable_expiration: bool = True
    enable_consolidation: bool = True
    enable_indexing: bool = True
    enable_versioning: bool = True
    enable_audit: bool = True


class IndexingConfig(BaseModel):
    """Configuration for memory indexing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index_content: bool = True
    index_metadata: bool = True
    index_tags: bool = True
    batch_size: int = 32
    embedding_dimensions: int = 384


class RetentionConfig(BaseModel):
    """Configuration for memory retention policies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    working_ttl_seconds: int = 3600
    session_ttl_seconds: int = 86400
    long_term_ttl_seconds: int = 2592000
    episodic_ttl_seconds: int = 604800
    semantic_ttl_seconds: int = 0
    max_working_count: int = 50
    max_session_count: int = 200
    archive_on_expire: bool = True


class ConsolidationConfig(BaseModel):
    """Configuration for memory consolidation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_memories_for_consolidation: int = 5
    consolidation_interval_seconds: int = 86400
    enable_episodic_to_semantic: bool = True
    enable_deduplication: bool = True
    max_summary_length: int = 500


class ConsolidationReport(BaseModel):
    """Report from a consolidation operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_count: int = 0
    consolidated_count: int = 0
    removed_count: int = 0
    summaries_generated: int = 0
    duration_ms: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ConsolidationConfig",
    "ConsolidationReport",
    "IndexingConfig",
    "MemoryConfig",
    "MemoryItem",
    "MemoryQuery",
    "MemoryRelation",
    "MemoryResult",
    "MemoryScope",
    "MemorySearchResult",
    "MemoryStatus",
    "MemoryType",
    "RetentionConfig",
    "ScopedMemoryId",
]
