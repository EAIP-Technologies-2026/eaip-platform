"""Semantic relationship service — inference, similarity, clustering."""

from __future__ import annotations

from typing import Any

from eaip.kgraph.events import InferredRelationshipCreated
from eaip.kgraph.exceptions import EntityNotFoundError
from eaip.kgraph.models import Entity
from eaip.logging.context import get_logger


class SemanticRelationshipService:
    """Service for inferring and discovering semantic relationships.

    Provides:
    - Implicit relationship inference via shared properties
    - Similarity computation (Jaccard) between entities
    - Entity clustering by connectivity
    - Suggestion of potential missing relationships
    """

    def __init__(self, graph: Any) -> None:
        self._graph = graph
        self._log = get_logger("eaip.kgraph.semantic")
        self._event_handlers: list[Any] = []

    def on(self, handler: Any) -> None:
        self._event_handlers.append(handler)

    async def _emit(self, event: Any) -> None:
        for handler in self._event_handlers:
            try:
                if callable(handler):
                    await handler(event)
            except Exception:
                self._log.warning("event.handler.failed", event_type=type(event).__name__)

    async def infer_relationships(
        self,
        entity_id: str,
        max_distance: int = 2,
    ) -> list[dict[str, Any]]:
        if entity_id not in self._graph.entities:
            raise EntityNotFoundError(
                f"Entity {entity_id} not found", context={"entity_id": entity_id}
            )
        source = self._graph.entities[entity_id]
        inferred: list[dict[str, Any]] = []

        for eid, target in self._graph.entities.items():
            if eid == entity_id:
                continue
            score = self._compute_shared_property_score(source, target)
            if score > 0:
                inferred.append(
                    {
                        "source_entity_id": entity_id,
                        "target_entity_id": eid,
                        "relationship_type": "shared_property",
                        "confidence": round(score, 4),
                    }
                )

        if max_distance > 1:
            seen = {entity_id}
            queue: list[tuple[str, int]] = [(entity_id, 0)]
            while queue:
                current_id, dist = queue.pop(0)
                if dist >= max_distance:
                    continue
                adj = self._graph.adjacency.get(current_id, {})
                for rel in adj.get("out", {}).values():
                    if rel.target_entity_id not in seen:
                        seen.add(rel.target_entity_id)
                        for eid, target in self._graph.entities.items():
                            if eid in (rel.target_entity_id, entity_id) or eid in seen:
                                continue
                            score = self._compute_shared_property_score(
                                self._graph.entities[rel.target_entity_id],
                                target,
                            )
                            if score > 0:
                                inferred.append(
                                    {
                                        "source_entity_id": rel.target_entity_id,
                                        "target_entity_id": eid,
                                        "relationship_type": "shared_property",
                                        "confidence": round(score, 4),
                                    }
                                )
                        queue.append((rel.target_entity_id, dist + 1))

        for inf in inferred:
            await self._emit(
                InferredRelationshipCreated(
                    source_entity_id=inf["source_entity_id"],
                    target_entity_id=inf["target_entity_id"],
                    relationship_type=inf["relationship_type"],
                    confidence=inf["confidence"],
                )
            )

        return inferred

    def _compute_shared_property_score(self, a: Entity, b: Entity) -> float:
        shared = set(a.properties.keys()) & set(b.properties.keys())
        if not shared:
            return 0.0
        matches = sum(1 for k in shared if a.properties[k] == b.properties[k])
        total = max(len(a.properties), len(b.properties))
        return matches / total if total > 0 else 0.0

    async def find_similar_entities(
        self,
        entity_id: str,
        threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        if entity_id not in self._graph.entities:
            raise EntityNotFoundError(
                f"Entity {entity_id} not found", context={"entity_id": entity_id}
            )
        self._graph.entities[entity_id]
        results: list[dict[str, Any]] = []

        for eid, target in self._graph.entities.items():
            if eid == entity_id:
                continue
            similarity = await self.compute_similarity(entity_id, eid)
            if similarity >= threshold:
                results.append(
                    {
                        "entity_id": eid,
                        "entity_name": target.name,
                        "entity_type": target.type,
                        "similarity": round(similarity, 4),
                    }
                )

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    async def compute_similarity(self, entity_a_id: str, entity_b_id: str) -> float:
        if entity_a_id not in self._graph.entities:
            raise EntityNotFoundError(
                f"Entity {entity_a_id} not found", context={"entity_id": entity_a_id}
            )
        if entity_b_id not in self._graph.entities:
            raise EntityNotFoundError(
                f"Entity {entity_b_id} not found", context={"entity_id": entity_b_id}
            )
        a = self._graph.entities[entity_a_id]
        b = self._graph.entities[entity_b_id]

        a_props = {
            str(v).lower() for v in a.properties.values() if isinstance(v, (str, int, float, bool))
        }
        b_props = {
            str(v).lower() for v in b.properties.values() if isinstance(v, (str, int, float, bool))
        }
        a_tags = {t.lower() for t in a.tags}
        b_tags = {t.lower() for t in b.tags}
        a_vals = a_props | a_tags
        b_vals = b_props | b_tags

        if not a_vals and not b_vals:
            return 0.0
        intersection = a_vals & b_vals
        union = a_vals | b_vals
        return len(intersection) / len(union) if union else 0.0

    async def get_entity_cluster(
        self,
        entity_type: str,
        min_connections: int = 2,
    ) -> list[list[str]]:
        type_entities = [eid for eid, e in self._graph.entities.items() if e.type == entity_type]
        if not type_entities:
            return []

        visited: set[str] = set()
        clusters: list[list[str]] = []

        for eid in type_entities:
            if eid in visited:
                continue
            cluster: list[str] = []
            stack = [eid]
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                cluster.append(current)
                adj = self._graph.adjacency.get(current, {})
                connected = set()
                for rel in adj.get("out", {}).values():
                    if rel.target_entity_id in type_entities:
                        connected.add(rel.target_entity_id)
                for rel in adj.get("in", {}).values():
                    if rel.source_entity_id in type_entities:
                        connected.add(rel.source_entity_id)
                for neighbor in connected:
                    if neighbor not in visited:
                        stack.append(neighbor)
            if len(cluster) >= min_connections:
                clusters.append(cluster)

        return clusters

    async def suggest_relationships(self, entity_id: str) -> list[dict[str, Any]]:
        if entity_id not in self._graph.entities:
            raise EntityNotFoundError(
                f"Entity {entity_id} not found", context={"entity_id": entity_id}
            )
        self._graph.entities[entity_id]
        existing_neighbors: set[str] = set()
        adj = self._graph.adjacency.get(entity_id, {})
        for rel in adj.get("out", {}).values():
            existing_neighbors.add(rel.target_entity_id)
        for rel in adj.get("in", {}).values():
            existing_neighbors.add(rel.source_entity_id)

        suggestions: list[dict[str, Any]] = []
        for eid, target in self._graph.entities.items():
            if eid == entity_id or eid in existing_neighbors:
                continue
            similarity = await self.compute_similarity(entity_id, eid)
            if similarity > 0:
                suggestions.append(
                    {
                        "source_entity_id": entity_id,
                        "target_entity_id": eid,
                        "target_name": target.name,
                        "target_type": target.type,
                        "similarity": round(similarity, 4),
                        "reason": "shared_properties" if similarity > 0.5 else "weak_similarity",
                    }
                )

        suggestions.sort(key=lambda x: x["similarity"], reverse=True)
        return suggestions


__all__ = ["SemanticRelationshipService"]
