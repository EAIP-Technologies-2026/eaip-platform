"""Semantic Indexing models — indexes, fields, documents, queries, configs."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class IndexStatus(StrEnum):
    """Status of a semantic index."""

    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REBUILDING = "rebuilding"
    OPTIMIZING = "optimizing"
    FAILED = "failed"
    DELETED = "deleted"


class FieldType(StrEnum):
    """Data type for an index field."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"
    KEYWORD = "keyword"
    VECTOR = "vector"
    NESTED = "nested"


class IndexField(BaseModel):
    """Definition of a single field within an index mapping."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: FieldType = FieldType.STRING
    indexed: bool = True
    stored: bool = True
    searchable: bool = True
    filterable: bool = False
    sortable: bool = False
    facetable: bool = False
    analyzer: str = ""
    synonym_maps: tuple[str, ...] = ()


class AnalyzerConfig(BaseModel):
    """Configuration for a text analyzer used during indexing and search."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    tokenizer: str = "standard"
    token_filters: tuple[str, ...] = ()
    char_filters: tuple[str, ...] = ()


class TokenizerConfig(BaseModel):
    """Configuration for a tokenizer used by an analyzer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: str = "standard"
    options: dict[str, Any] = Field(default_factory=dict)


class SynonymMap(BaseModel):
    """A mapping of equivalent terms used during query expansion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    synonyms: tuple[str, ...] = ()
    format: str = "solr"


class StopWordsList(BaseModel):
    """A list of stop words to exclude from indexing and search."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    words: tuple[str, ...] = ()
    language: str = ""


class IndexMapping(BaseModel):
    """Mapping definition for a semantic index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fields: tuple[IndexField, ...] = ()
    analyzers: tuple[AnalyzerConfig, ...] = ()
    tokenizers: tuple[TokenizerConfig, ...] = ()
    synonym_maps: tuple[SynonymMap, ...] = ()
    stop_words: tuple[StopWordsList, ...] = ()


class IndexConfig(BaseModel):
    """Configuration for a semantic index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    mapping: IndexMapping = Field(default_factory=IndexMapping)
    shard_count: int = 1
    replica_count: int = 1
    max_documents: int = 0
    embedding_dimensions: int = 0
    similarity_metric: str = "cosine"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticIndex(BaseModel):
    """A semantic index instance with its current status and configuration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index_id: str
    config: IndexConfig
    status: IndexStatus = IndexStatus.CREATING
    document_count: int = 0
    size_bytes: int = 0
    last_rebuilt_at: datetime | None = None
    last_optimized_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class IndexDocument(BaseModel):
    """A document that is indexed within a semantic index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    index_id: str
    fields: tuple[IndexedField, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class IndexedField(BaseModel):
    """A single indexed field value within a document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    value: str = ""
    vector: tuple[float, ...] = ()


class IndexEntry(BaseModel):
    """An entry in the index representing a token with its postings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    term: str
    field: str = ""
    document_ids: tuple[str, ...] = ()
    term_frequency: int = 0
    positions: tuple[int, ...] = ()


class IndexQuery(BaseModel):
    """A query against a semantic index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str = ""
    index_id: str = ""
    top_k: int = 10
    offset: int = 0
    filters: dict[str, Any] = Field(default_factory=dict)
    vector: tuple[float, ...] = ()
    alpha: float = 1.0
    include_vectors: bool = False
    search_fields: tuple[str, ...] = ()
    scoring_profile: str = ""


class IndexQueryResult(BaseModel):
    """Result of a query execution against a semantic index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str = ""
    index_id: str = ""
    documents: tuple[IndexDocument, ...] = ()
    total_hits: int = 0
    duration_ms: float = 0.0
    max_score: float = 0.0


class IndexStats(BaseModel):
    """Statistics about a semantic index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index_id: str
    document_count: int = 0
    total_fields: int = 0
    indexed_fields: int = 0
    size_bytes: int = 0
    segment_count: int = 0
    deleted_document_count: int = 0


class IndexRebuildPlan(BaseModel):
    """A plan for rebuilding a semantic index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index_id: str
    reason: str = ""
    estimated_document_count: int = 0
    estimated_size_bytes: int = 0
    preserve_existing: bool = False
    optimize_after_rebuild: bool = True


class IndexingPipelineConfig(BaseModel):
    """Configuration for the indexing pipeline."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    batch_size: int = 100
    max_concurrent: int = 4
    retry_attempts: int = 3
    retry_delay_ms: int = 1000
    commit_interval_ms: int = 5000
    auto_commit: bool = True


class IndexMetrics(BaseModel):
    """Metrics collected for a semantic index operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index_id: str
    operation: str = ""
    documents_processed: int = 0
    documents_failed: int = 0
    total_duration_ms: float = 0.0
    avg_document_time_ms: float = 0.0
    throughput_dps: float = 0.0
    memory_bytes: int = 0
    timestamp: datetime = Field(default_factory=utc_now)


__all__ = [
    "AnalyzerConfig",
    "FieldType",
    "IndexConfig",
    "IndexDocument",
    "IndexEntry",
    "IndexField",
    "IndexMapping",
    "IndexMetrics",
    "IndexQuery",
    "IndexQueryResult",
    "IndexRebuildPlan",
    "IndexStats",
    "IndexStatus",
    "IndexedField",
    "IndexingPipelineConfig",
    "SemanticIndex",
    "StopWordsList",
    "SynonymMap",
    "TokenizerConfig",
]
