"""Graph traversal service — BFS, DFS, shortest path, subgraph, cycle detection."""

from __future__ import annotations

from collections import deque
from typing import Any, Callable

from eaip.kgraph.exceptions import GraphTraversalError
from eaip.kgraph.models import Entity, Relationship
from eaip.logging.context import get_logger

Predicate = Callable[[Entity, Relationship | None], bool] | None


class GraphTraversalService:
    """Provides graph traversal algorithms for the knowledge graph.

    Operates on a graph that exposes ``entities``, ``relationships``,
    and ``adjacency`` attributes (e.g. :class:`KnowledgeGraph`).
    """

    def __init__(self, graph: Any) -> None:
        self._graph = graph
        self._log = get_logger("eaip.kgraph.traversal")

    def _get_neighbor_ids(
        self, entity_id: str, direction: str, predicate: Predicate = None, rel_types: tuple[str, ...] | None = None,
    ) -> list[tuple[str, str]]:
        """Return list of (neighbor_id, relationship_id) pairs."""
        results: list[tuple[str, str]] = []
        adj = self._graph.adjacency.get(entity_id, {})

        if direction in ("out", "both"):
            for rel_id, rel in adj.get("out", {}).items():
                if rel_types and rel.type not in rel_types:
                    continue
                e = self._graph.entities.get(rel.target_entity_id)
                if e and (predicate is None or predicate(e, rel)):
                    results.append((rel.target_entity_id, rel_id))

        if direction in ("in", "both"):
            for rel_id, rel in adj.get("in", {}).items():
                if rel_types and rel.type not in rel_types:
                    continue
                e = self._graph.entities.get(rel.source_entity_id)
                if e and (predicate is None or predicate(e, rel)):
                    results.append((rel.source_entity_id, rel_id))

        return results

    async def bfs(
        self,
        start_id: str,
        max_depth: int = 10,
        predicate: Predicate = None,
        direction: str = "out",
        rel_types: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        if start_id not in self._graph.entities:
            raise GraphTraversalError(f"Start entity {start_id} not found", context={"entity_id": start_id})
        visited: set[str] = {start_id}
        entity_ids: list[str] = [start_id]
        relationship_ids: list[str] = []
        queue: deque[tuple[str, int]] = deque([(start_id, 0)])

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor_id, rel_id in self._get_neighbor_ids(current_id, direction, predicate, rel_types):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    entity_ids.append(neighbor_id)
                    relationship_ids.append(rel_id)
                    queue.append((neighbor_id, depth + 1))

        return {"entity_ids": entity_ids, "relationship_ids": relationship_ids, "paths": []}

    async def dfs(
        self,
        start_id: str,
        max_depth: int = 10,
        predicate: Predicate = None,
        direction: str = "out",
        rel_types: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        if start_id not in self._graph.entities:
            raise GraphTraversalError(f"Start entity {start_id} not found", context={"entity_id": start_id})
        visited: set[str] = {start_id}
        entity_ids: list[str] = [start_id]
        relationship_ids: list[str] = []
        stack: list[tuple[str, int]] = [(start_id, 0)]

        while stack:
            current_id, depth = stack.pop()
            if depth >= max_depth:
                continue
            for neighbor_id, rel_id in self._get_neighbor_ids(current_id, direction, predicate, rel_types):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    entity_ids.append(neighbor_id)
                    relationship_ids.append(rel_id)
                    stack.append((neighbor_id, depth + 1))

        return {"entity_ids": entity_ids, "relationship_ids": relationship_ids, "paths": []}

    async def shortest_path(
        self, source_id: str, target_id: str, max_depth: int = 10,
    ) -> dict[str, Any]:
        if source_id not in self._graph.entities:
            raise GraphTraversalError(f"Source entity {source_id} not found", context={"entity_id": source_id})
        if target_id not in self._graph.entities:
            raise GraphTraversalError(f"Target entity {target_id} not found", context={"entity_id": target_id})
        if source_id == target_id:
            return {
                "entity_ids": [source_id],
                "relationship_ids": [],
                "paths": [{"entity_ids": (source_id,), "relationship_ids": (), "total_weight": 0.0, "length": 0}],
            }
        visited: set[str] = {source_id}
        queue: deque[tuple[str, int, list[str], list[str], float]] = deque([(source_id, 0, [source_id], [], 0.0)])

        while queue:
            current_id, depth, path_entities, path_rels, total_weight = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor_id, rel_id in self._get_neighbor_ids(current_id, "both"):
                if neighbor_id not in visited:
                    rel = self._graph.relationships.get(rel_id)
                    w = total_weight + (rel.weight if rel else 1.0)
                    new_path = path_entities + [neighbor_id]
                    new_rels = path_rels + [rel_id]
                    if neighbor_id == target_id:
                        return {
                            "entity_ids": new_path,
                            "relationship_ids": new_rels,
                            "paths": [{
                                "entity_ids": tuple(new_path),
                                "relationship_ids": tuple(new_rels),
                                "total_weight": round(w, 4),
                                "length": len(new_rels),
                            }],
                        }
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1, new_path, new_rels, w))

        return {"entity_ids": [], "relationship_ids": [], "paths": []}

    async def get_subgraph(self, entity_ids: list[str], depth: int = 1) -> dict[str, Any]:
        result_entities: set[str] = set(entity_ids)
        result_rels: set[str] = set()

        for eid in entity_ids:
            if eid not in self._graph.entities:
                continue
            q: deque[tuple[str, int]] = deque([(eid, 0)])
            local_visited: set[str] = {eid}
            while q:
                current_id, d = q.popleft()
                if d >= depth:
                    continue
                for neighbor_id, rel_id in self._get_neighbor_ids(current_id, "both"):
                    result_rels.add(rel_id)
                    result_entities.add(neighbor_id)
                    if neighbor_id not in local_visited:
                        local_visited.add(neighbor_id)
                        q.append((neighbor_id, d + 1))

        return {
            "entity_ids": list(result_entities),
            "relationship_ids": list(result_rels),
            "paths": [],
        }

    async def find_paths_with_condition(
        self,
        start_id: str,
        target_type: str,
        rel_types: tuple[str, ...] | None = None,
        max_depth: int = 10,
    ) -> list[dict[str, Any]]:
        if start_id not in self._graph.entities:
            raise GraphTraversalError(f"Start entity {start_id} not found", context={"entity_id": start_id})
        paths: list[dict[str, Any]] = []
        stack: list[tuple[str, int, list[str], list[str]]] = [(start_id, 0, [start_id], [])]

        while stack:
            current_id, depth, path_entities, path_rels = stack.pop()
            if depth >= max_depth:
                continue
            for neighbor_id, rel_id in self._get_neighbor_ids(current_id, "both", rel_types=rel_types):
                new_path = path_entities + [neighbor_id]
                new_rels = path_rels + [rel_id]
                neighbor_entity = self._graph.entities.get(neighbor_id)
                if neighbor_entity and neighbor_entity.type == target_type:
                    paths.append({
                        "entity_ids": tuple(new_path),
                        "relationship_ids": tuple(new_rels),
                    })
                else:
                    stack.append((neighbor_id, depth + 1, new_path, new_rels))

        return paths

    async def detect_cycles(self, entity_id: str, max_depth: int = 10) -> list[list[str]]:
        if entity_id not in self._graph.entities:
            raise GraphTraversalError(f"Entity {entity_id} not found", context={"entity_id": entity_id})
        cycles: list[list[str]] = []
        stack: list[tuple[str, int, list[str]]] = [(entity_id, 0, [entity_id])]

        while stack:
            current_id, depth, path = stack.pop()
            if depth >= max_depth:
                continue
            for neighbor_id, _ in self._get_neighbor_ids(current_id, "out"):
                if neighbor_id == entity_id and len(path) > 1:
                    cycles.append(path + [entity_id])
                elif neighbor_id not in path:
                    stack.append((neighbor_id, depth + 1, path + [neighbor_id]))

        return cycles

    async def compute_centrality(self, entity_id: str, max_depth: int = 3) -> dict[str, Any]:
        if entity_id not in self._graph.entities:
            raise GraphTraversalError(f"Entity {entity_id} not found", context={"entity_id": entity_id})
        result = await self.bfs(entity_id, max_depth)
        reachable = len(result["entity_ids"]) - 1
        total = len(self._graph.entities) - 1
        centrality = reachable / total if total > 0 else 0.0
        return {
            "entity_id": entity_id,
            "reachable_nodes": reachable,
            "total_nodes": total + 1,
            "centrality": round(centrality, 6),
            "depth": max_depth,
        }


__all__ = ["GraphTraversalService"]
