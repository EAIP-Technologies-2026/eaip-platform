"""Knowledge Graph models — entities, relationships, queries, results, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class Entity(BaseModel):
    """A node in the knowledge graph representing a real-world entity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    name: str
    description: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    source: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: tuple[str, ...] = ()


class Relationship(BaseModel):
    """A typed, directed edge connecting two entities in the graph."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str
    source_entity_id: str
    target_entity_id: str
    properties: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=utc_now)
    bidirectional: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphQueryMode(StrEnum):
    """Supported graph traversal and query modes."""

    BFS = "bfs"
    DFS = "dfs"
    SHORTEST_PATH = "shortest_path"
    SUBGRAPH = "subgraph"


class GraphQuery(BaseModel):
    """A query targeting the knowledge graph."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str = ""
    entity_types: tuple[str, ...] = ()
    relationship_types: tuple[str, ...] = ()
    max_depth: int = Field(default=3, ge=0)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=100, ge=0)
    filters: dict[str, Any] = Field(default_factory=dict)
    mode: GraphQueryMode = GraphQueryMode.BFS
    start_entity_id: str = ""


class Path(BaseModel):
    """An ordered sequence of entities and relationships forming a path."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_ids: tuple[str, ...] = ()
    relationship_ids: tuple[str, ...] = ()
    total_weight: float = 0.0
    length: int = 0


class GraphResult(BaseModel):
    """The result of executing a graph query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entities: tuple[Entity, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    paths: tuple[Path, ...] = ()
    total_count: int = 0
    duration_ms: float = 0.0


class PersistenceType(StrEnum):
    """Supported persistence backends for the knowledge graph."""

    MEMORY = "memory"
    FILE = "file"
    DATABASE = "database"


class GraphConfig(BaseModel):
    """Configuration for the knowledge graph runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_indexing: bool = True
    index_entity_types: tuple[str, ...] = ()
    max_traversal_depth: int = Field(default=10, ge=0)
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(default=300, ge=0)
    persistence_type: PersistenceType = PersistenceType.MEMORY


class EntityIndex(BaseModel):
    """An inverted index mapping values to entity IDs for a given type/field."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_type: str
    field: str
    values: dict[str, list[str]] = Field(default_factory=dict)


class GraphStats(BaseModel):
    """Aggregate statistics about the graph's current state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_entities: int = 0
    total_relationships: int = 0
    entity_type_counts: dict[str, int] = Field(default_factory=dict)
    relationship_type_counts: dict[str, int] = Field(default_factory=dict)
    avg_degree: float = 0.0
    density: float = 0.0
    last_updated: datetime = Field(default_factory=utc_now)


__all__ = [
    "Entity",
    "EntityIndex",
    "GraphConfig",
    "GraphQuery",
    "GraphQueryMode",
    "GraphResult",
    "GraphStats",
    "Path",
    "PersistenceType",
    "Relationship",
]
