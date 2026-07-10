"""Knowledge Graph — in-memory graph store with adjacency lists."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

from eaip.kgraph.events import (
    EntityAdded,
    EntityDeleted,
    EntityUpdated,
    GraphQueryExecuted,
    GraphTraversalExecuted,
    RelationshipAdded,
    RelationshipDeleted,
    RelationshipUpdated,
)
from eaip.kgraph.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    GraphQueryError,
    RelationshipNotFoundError,
)
from eaip.kgraph.models import (
    Entity,
    GraphQuery,
    GraphQueryMode,
    GraphResult,
    GraphStats,
    Path,
    Relationship,
)
from eaip.kgraph.traversal import GraphTraversalService
from eaip.logging.context import get_logger


class KnowledgeGraph:
    """In-memory knowledge graph with adjacency list storage.

    Supports entity/relationship CRUD, graph traversal (BFS, DFS,
    shortest path, subgraph), property-based search, and query execution.
    """

    def __init__(self, config: Any | None = None) -> None:
        self._log = get_logger("eaip.kgraph.graph")
        self._entities: dict[str, Entity] = {}
        self._relationships: dict[str, Relationship] = {}

        # adjacency: entity_id -> {direction: {rel_id: Relationship}}
        self._adjacency: dict[str, dict[str, dict[str, Relationship]]] = defaultdict(
            lambda: {"out": {}, "in": {}}
        )

        # entity type index: entity_type -> set of entity_ids
        self._type_index: dict[str, set[str]] = defaultdict(set)

        self._traversal = GraphTraversalService(self)
        self._event_handlers: list[Any] = []
        self._config = config

    # ── entity CRUD ──────────────────────────────────────────────

    async def add_entity(self, entity: Entity) -> Entity:
        if not entity.id or not entity.type:
            raise EntityValidationError("Entity id and type are required")
        if entity.id in self._entities:
            raise EntityValidationError(f"Entity {entity.id} already exists")
        self._entities[entity.id] = entity
        self._type_index[entity.type].add(entity.id)
        self._log.debug("entity.added", id=entity.id, type=entity.type)
        await self._emit(EntityAdded(entity_id=entity.id, entity_type=entity.type, entity_name=entity.name))
        return entity

    async def get_entity(self, entity_id: str) -> Entity:
        entity = self._entities.get(entity_id)
        if entity is None:
            raise EntityNotFoundError(f"Entity {entity_id} not found", context={"entity_id": entity_id})
        return entity

    async def update_entity(self, entity_id: str, updates: dict[str, Any]) -> Entity:
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"Entity {entity_id} not found", context={"entity_id": entity_id})
        current = self._entities[entity_id]
        allowed = {"name", "description", "properties", "confidence", "source", "metadata", "tags"}
        invalid = set(updates) - allowed
        if invalid:
            raise EntityValidationError(f"Invalid fields: {invalid}", context={"fields": list(invalid)})
        merged_props = {**current.properties, **updates.get("properties", {})}
        merged_meta = {**current.metadata, **updates.get("metadata", {})}
        updated = current.model_copy(update={
            "name": updates.get("name", current.name),
            "description": updates.get("description", current.description),
            "properties": merged_props,
            "confidence": updates.get("confidence", current.confidence),
            "source": updates.get("source", current.source),
            "metadata": merged_meta,
            "tags": updates.get("tags", current.tags),
            "updated_at": time.time(),
        })
        self._entities[entity_id] = updated

        if "type" in updates or "updated_at" in updates:
            pass

        self._log.debug("entity.updated", id=entity_id)
        await self._emit(EntityUpdated(entity_id=entity_id, entity_type=current.type, changes=updates))
        return updated

    async def delete_entity(self, entity_id: str, cascade: bool = False) -> None:
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"Entity {entity_id} not found", context={"entity_id": entity_id})
        entity = self._entities[entity_id]
        if cascade:
            to_remove = list(self._adjacency[entity_id]["out"].keys()) + list(self._adjacency[entity_id]["in"].keys())
            for rel_id in to_remove:
                await self.delete_relationship(rel_id)
        else:
            rels = list(self._adjacency[entity_id]["out"].values()) + list(self._adjacency[entity_id]["in"].values())
            if rels:
                raise EntityValidationError(
                    f"Entity {entity_id} has relationships; use cascade=True to delete",
                    context={"relationship_count": len(rels)},
                )
        self._type_index[entity.type].discard(entity_id)
        del self._entities[entity_id]
        self._adjacency.pop(entity_id, None)
        self._log.debug("entity.deleted", id=entity_id, cascade=cascade)
        await self._emit(EntityDeleted(entity_id=entity_id, entity_type=entity.type, cascade=cascade))

    # ── relationship CRUD ────────────────────────────────────────

    async def add_relationship(self, rel: Relationship) -> Relationship:
        if rel.source_entity_id not in self._entities:
            raise EntityNotFoundError(
                f"Source entity {rel.source_entity_id} not found",
                context={"entity_id": rel.source_entity_id},
            )
        if rel.target_entity_id not in self._entities:
            raise EntityNotFoundError(
                f"Target entity {rel.target_entity_id} not found",
                context={"entity_id": rel.target_entity_id},
            )
        if rel.id in self._relationships:
            raise EntityValidationError(f"Relationship {rel.id} already exists")
        self._relationships[rel.id] = rel
        self._adjacency[rel.source_entity_id]["out"][rel.id] = rel
        self._adjacency[rel.target_entity_id]["in"][rel.id] = rel
        if rel.bidirectional:
            self._adjacency[rel.target_entity_id]["out"][rel.id] = rel
            self._adjacency[rel.source_entity_id]["in"][rel.id] = rel
        self._log.debug("relationship.added", id=rel.id, type=rel.type)
        await self._emit(RelationshipAdded(
            relationship_id=rel.id,
            relationship_type=rel.type,
            source_entity_id=rel.source_entity_id,
            target_entity_id=rel.target_entity_id,
        ))
        return rel

    async def get_relationship(self, rel_id: str) -> Relationship:
        rel = self._relationships.get(rel_id)
        if rel is None:
            raise RelationshipNotFoundError(f"Relationship {rel_id} not found", context={"relationship_id": rel_id})
        return rel

    async def update_relationship(self, rel_id: str, updates: dict[str, Any]) -> Relationship:
        if rel_id not in self._relationships:
            raise RelationshipNotFoundError(f"Relationship {rel_id} not found", context={"relationship_id": rel_id})
        current = self._relationships[rel_id]
        allowed = {"type", "properties", "weight", "bidirectional", "metadata"}
        invalid = set(updates) - allowed
        if invalid:
            raise EntityValidationError(f"Invalid fields: {invalid}", context={"fields": list(invalid)})
        merged_props = {**current.properties, **updates.get("properties", {})}
        merged_meta = {**current.metadata, **updates.get("metadata", {})}
        updated = current.model_copy(update={
            "type": updates.get("type", current.type),
            "properties": merged_props,
            "weight": updates.get("weight", current.weight),
            "bidirectional": updates.get("bidirectional", current.bidirectional),
            "metadata": merged_meta,
        })
        self._relationships[rel_id] = updated
        self._rebuild_adjacency_for_rel(rel_id, updated)
        self._log.debug("relationship.updated", id=rel_id)
        await self._emit(RelationshipUpdated(
            relationship_id=rel_id,
            relationship_type=current.type,
            changes=updates,
        ))
        return updated

    async def delete_relationship(self, rel_id: str) -> None:
        if rel_id not in self._relationships:
            raise RelationshipNotFoundError(f"Relationship {rel_id} not found", context={"relationship_id": rel_id})
        rel = self._relationships.pop(rel_id)
        self._adjacency[rel.source_entity_id]["out"].pop(rel_id, None)
        self._adjacency[rel.target_entity_id]["in"].pop(rel_id, None)
        if rel.bidirectional:
            self._adjacency[rel.target_entity_id]["out"].pop(rel_id, None)
            self._adjacency[rel.source_entity_id]["in"].pop(rel_id, None)
        self._log.debug("relationship.deleted", id=rel_id)
        await self._emit(RelationshipDeleted(relationship_id=rel_id, relationship_type=rel.type))

    def _rebuild_adjacency_for_rel(self, rel_id: str, rel: Relationship) -> None:
        for eid in (rel.source_entity_id, rel.target_entity_id):
            self._adjacency[eid]["out"].pop(rel_id, None)
            self._adjacency[eid]["in"].pop(rel_id, None)
        self._adjacency[rel.source_entity_id]["out"][rel_id] = rel
        self._adjacency[rel.target_entity_id]["in"][rel_id] = rel
        if rel.bidirectional:
            self._adjacency[rel.target_entity_id]["out"][rel_id] = rel
            self._adjacency[rel.source_entity_id]["in"][rel_id] = rel

    # ── query ───────────────────────────────────────────────────

    async def query(self, query: GraphQuery) -> GraphResult:
        t0 = time.monotonic()
        mode = query.mode
        start_id = query.start_entity_id

        if mode is GraphQueryMode.BFS:
            if not start_id:
                raise GraphQueryError("start_entity_id required for BFS mode")
            result = await self._traversal.bfs(
                start_id, query.max_depth,
                predicate=self._make_predicate(query),
            )
        elif mode is GraphQueryMode.DFS:
            if not start_id:
                raise GraphQueryError("start_entity_id required for DFS mode")
            result = await self._traversal.dfs(
                start_id, query.max_depth,
                predicate=self._make_predicate(query),
            )
        elif mode is GraphQueryMode.SHORTEST_PATH:
            target_id = query.filters.get("target_entity_id", "")
            if not start_id or not target_id:
                raise GraphQueryError("start_entity_id and target_entity_id filter required for shortest_path mode")
            result = await self._traversal.shortest_path(start_id, target_id, query.max_depth)
        elif mode is GraphQueryMode.SUBGRAPH:
            entity_ids = query.filters.get("entity_ids", [])
            if not entity_ids:
                raise GraphQueryError("entity_ids filter required for subgraph mode")
            result = await self._traversal.get_subgraph(list(entity_ids), query.max_depth)
        else:
            raise GraphQueryError(f"Unsupported query mode: {mode}")

        entities_set: dict[str, Entity] = {}
        rels_set: dict[str, Relationship] = {}
        paths: list[Path] = []

        for entity_id in result.get("entity_ids", []):
            try:
                entities_set[entity_id] = await self.get_entity(entity_id)
            except EntityNotFoundError:
                pass
        for rel_id in result.get("relationship_ids", []):
            try:
                rels_set[rel_id] = await self.get_relationship(rel_id)
            except RelationshipNotFoundError:
                pass
        for p_data in result.get("paths", []):
            paths.append(Path(**p_data))

        duration_ms = (time.monotonic() - t0) * 1000
        graph_result = GraphResult(
            entities=tuple(entities_set.values()),
            relationships=tuple(rels_set.values()),
            paths=tuple(paths),
            total_count=len(entities_set),
            duration_ms=duration_ms,
        )

        await self._emit(GraphQueryExecuted(
            query_mode=mode.value,
            result_count=graph_result.total_count,
            duration_ms=duration_ms,
        ))
        return graph_result

    def _make_predicate(self, query: GraphQuery) -> Any:
        def predicate(entity: Entity, rel: Relationship | None) -> bool:
            if query.entity_types and entity.type not in query.entity_types:
                return False
            if rel and query.relationship_types and rel.type not in query.relationship_types:
                return False
            if entity.confidence < query.min_confidence:
                return False
            if query.filters:
                for key, value in query.filters.items():
                    if key in ("target_entity_id", "entity_ids"):
                        continue
                    if key in entity.properties and entity.properties[key] != value:
                        return False
            return True
        return predicate

    # ── traversal wrappers ───────────────────────────────────────

    async def traverse(self, entity_id: str, depth: int, direction: str = "out") -> dict[str, Any]:
        result = await self._traversal.bfs(entity_id, depth, direction=direction)
        await self._emit(GraphTraversalExecuted(
            start_entity_id=entity_id,
            depth=depth,
            direction=direction,
            nodes_visited=len(result.get("entity_ids", [])),
        ))
        return result

    async def get_neighbors(self, entity_id: str, rel_types: tuple[str, ...] | None = None) -> list[Entity]:
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"Entity {entity_id} not found", context={"entity_id": entity_id})
        neighbors: list[Entity] = []
        seen: set[str] = set()
        for rel in self._adjacency[entity_id]["out"].values():
            if rel_types and rel.type not in rel_types:
                continue
            if rel.target_entity_id not in seen:
                seen.add(rel.target_entity_id)
                neighbors.append(self._entities[rel.target_entity_id])
        return neighbors

    async def get_shortest_path(self, source_id: str, target_id: str, max_depth: int = 10) -> Path | None:
        result = await self._traversal.shortest_path(source_id, target_id, max_depth)
        if not result.get("paths"):
            return None
        return Path(**result["paths"][0])

    async def find_entities_by_type(self, entity_type: str) -> list[Entity]:
        return [self._entities[eid] for eid in self._type_index.get(entity_type, set()) if eid in self._entities]

    async def find_entities_by_property(self, key: str, value: Any) -> list[Entity]:
        return [e for e in self._entities.values() if e.properties.get(key) == value]

    async def get_subgraph(self, entity_ids: list[str], depth: int = 1) -> dict[str, Any]:
        return await self._traversal.get_subgraph(entity_ids, depth)

    # ── stats ────────────────────────────────────────────────────

    async def get_stats(self) -> GraphStats:
        total_entities = len(self._entities)
        total_rels = len(self._relationships)
        entity_type_counts: dict[str, int] = {}
        for e in self._entities.values():
            entity_type_counts[e.type] = entity_type_counts.get(e.type, 0) + 1
        rel_type_counts: dict[str, int] = {}
        for r in self._relationships.values():
            rel_type_counts[r.type] = rel_type_counts.get(r.type, 0) + 1
        degree_sum = sum(
            len(self._adjacency[eid]["out"]) + len(self._adjacency[eid]["in"])
            for eid in self._entities
        )
        avg_degree = degree_sum / total_entities if total_entities else 0.0
        max_possible = total_entities * (total_entities - 1) if total_entities > 1 else 1
        density = total_rels / max_possible if max_possible else 0.0
        return GraphStats(
            total_entities=total_entities,
            total_relationships=total_rels,
            entity_type_counts=entity_type_counts,
            relationship_type_counts=rel_type_counts,
            avg_degree=round(avg_degree, 4),
            density=round(density, 6),
            last_updated=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )

    # ── events ───────────────────────────────────────────────────

    def on(self, handler: Any) -> None:
        self._event_handlers.append(handler)

    async def _emit(self, event: Any) -> None:
        for handler in self._event_handlers:
            try:
                if hasattr(handler, "__call__"):
                    await handler(event)
            except Exception:
                self._log.warning("event.handler.failed", event_type=type(event).__name__)

    # ── internal access for traversal/index ──────────────────────

    @property
    def entities(self) -> dict[str, Entity]:
        return self._entities

    @property
    def relationships(self) -> dict[str, Relationship]:
        return self._relationships

    @property
    def adjacency(self) -> dict[str, dict[str, dict[str, Relationship]]]:
        return self._adjacency

    @property
    def traversal_service(self) -> GraphTraversalService:
        return self._traversal


__all__ = ["KnowledgeGraph"]
