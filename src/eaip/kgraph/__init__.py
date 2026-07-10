"""Knowledge Graph Runtime — entity/relationship models, graph traversal,
queries, indexing, persistence abstractions, and runtime integration.

Bundle-039 of the EAIP Platform Foundation Milestone.

Extends the existing Knowledge Engine with enterprise knowledge graph
capabilities including:
- Entity and Relationship models with metadata and confidence scoring
- Graph traversal (BFS, DFS, shortest path, subgraph extraction)
- Inverted-index-based search for entities and relationships
- Semantic relationship inference, similarity computation, and clustering
- Health check, capability, and RuntimeModule integration
"""

from __future__ import annotations

from eaip.kgraph.events import (
    EntityAdded,
    EntityDeleted,
    EntityUpdated,
    GraphIndexRebuilt,
    GraphQueryExecuted,
    GraphTraversalExecuted,
    InferredRelationshipCreated,
    RelationshipAdded,
    RelationshipDeleted,
    RelationshipUpdated,
)
from eaip.kgraph.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    GraphError,
    GraphQueryError,
    GraphTraversalError,
    RelationshipNotFoundError,
)
from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.health import GraphHealthCheck
from eaip.kgraph.index import GraphIndex
from eaip.kgraph.integration import GraphRuntimeModule
from eaip.kgraph.models import (
    Entity,
    EntityIndex,
    GraphConfig,
    GraphQuery,
    GraphResult,
    GraphStats,
    Path,
    Relationship,
)
from eaip.kgraph.semantic import SemanticRelationshipService
from eaip.kgraph.traversal import GraphTraversalService

__all__ = [
    "Entity",
    "EntityAdded",
    "EntityDeleted",
    "EntityIndex",
    "EntityNotFoundError",
    "EntityUpdated",
    "EntityValidationError",
    "GraphConfig",
    "GraphError",
    "GraphHealthCheck",
    "GraphIndex",
    "GraphIndexRebuilt",
    "GraphQuery",
    "GraphQueryError",
    "GraphQueryExecuted",
    "GraphResult",
    "GraphRuntimeModule",
    "GraphStats",
    "GraphTraversalError",
    "GraphTraversalExecuted",
    "GraphTraversalService",
    "InferredRelationshipCreated",
    "KnowledgeGraph",
    "Path",
    "Relationship",
    "RelationshipAdded",
    "RelationshipDeleted",
    "RelationshipNotFoundError",
    "RelationshipUpdated",
    "SemanticRelationshipService",
]
