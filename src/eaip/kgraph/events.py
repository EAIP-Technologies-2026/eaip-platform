"""Knowledge Graph domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class GraphEvent(DomainEvent):
    """Base event for all Knowledge Graph events."""

    event_type: ClassVar[str] = "eaip.kgraph.event"


class EntityAdded(GraphEvent):
    """Published when an entity is added to the graph."""

    event_type: ClassVar[str] = "eaip.kgraph.entity.added"
    entity_id: str
    entity_type: str
    entity_name: str


class EntityUpdated(GraphEvent):
    """Published when an entity is updated."""

    event_type: ClassVar[str] = "eaip.kgraph.entity.updated"
    entity_id: str
    entity_type: str
    changes: dict[str, Any]


class EntityDeleted(GraphEvent):
    """Published when an entity is deleted from the graph."""

    event_type: ClassVar[str] = "eaip.kgraph.entity.deleted"
    entity_id: str
    entity_type: str
    cascade: bool = False


class RelationshipAdded(GraphEvent):
    """Published when a relationship is added to the graph."""

    event_type: ClassVar[str] = "eaip.kgraph.relationship.added"
    relationship_id: str
    relationship_type: str
    source_entity_id: str
    target_entity_id: str


class RelationshipUpdated(GraphEvent):
    """Published when a relationship is updated."""

    event_type: ClassVar[str] = "eaip.kgraph.relationship.updated"
    relationship_id: str
    relationship_type: str
    changes: dict[str, Any]


class RelationshipDeleted(GraphEvent):
    """Published when a relationship is deleted."""

    event_type: ClassVar[str] = "eaip.kgraph.relationship.deleted"
    relationship_id: str
    relationship_type: str


class GraphQueryExecuted(GraphEvent):
    """Published after a graph query is executed."""

    event_type: ClassVar[str] = "eaip.kgraph.query.executed"
    query_mode: str
    result_count: int
    duration_ms: float


class GraphTraversalExecuted(GraphEvent):
    """Published after a graph traversal is performed."""

    event_type: ClassVar[str] = "eaip.kgraph.traversal.executed"
    start_entity_id: str
    depth: int
    direction: str
    nodes_visited: int


class GraphIndexRebuilt(GraphEvent):
    """Published when the graph index is rebuilt."""

    event_type: ClassVar[str] = "eaip.kgraph.index.rebuilt"
    entity_count: int
    relationship_count: int


class InferredRelationshipCreated(GraphEvent):
    """Published when a relationship is inferred by the semantic service."""

    event_type: ClassVar[str] = "eaip.kgraph.inferred_relationship.created"
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    confidence: float


__all__ = [
    "EntityAdded",
    "EntityDeleted",
    "EntityUpdated",
    "GraphEvent",
    "GraphIndexRebuilt",
    "GraphQueryExecuted",
    "GraphTraversalExecuted",
    "InferredRelationshipCreated",
    "RelationshipAdded",
    "RelationshipDeleted",
    "RelationshipUpdated",
]
