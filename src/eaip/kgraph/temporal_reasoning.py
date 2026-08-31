from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.models import Entity, Relationship


class TemporalReasoningService:
    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self._graph = graph or KnowledgeGraph()

    async def add_entity_with_temporal(self, entity: Entity, tenant_id: str = "default", valid_from: datetime | None = None, valid_until: datetime | None = None) -> Entity:
        entity = entity.model_copy(update={"metadata": {**entity.metadata, "tenant_id": tenant_id, "valid_from": (valid_from or datetime.now(UTC)).isoformat(), "valid_until": valid_until.isoformat() if valid_until else None}})
        await self._graph.add_entity(entity)
        return entity

    async def path_discovery(self, source_id: str, target_id: str, max_depth: int = 4) -> list[list[str]]:
        # BFS to find paths
        graph = self._graph
        # fallback: use graph traversal if available
        try:
            result = await graph.query({"mode": "shortest_path", "start_entity_id": source_id, "limit": 10, "max_depth": max_depth})
            if result and result.paths:
                return [list(p.entity_ids) for p in result.paths]
        except Exception:
            pass
        return []

    async def dependency_analysis(self, entity_id: str, tenant_id: str = "default") -> list[str]:
        # entities that depend on this entity (incoming edges)
        try:
            rels = await self._graph.list_relationships(entity_id) if hasattr(self._graph, "list_relationships") else []
        except Exception:
            rels = []
        return [r.source_entity_id for r in rels if r.target_entity_id == entity_id]

    async def impact_analysis(self, entity_id: str, tenant_id: str = "default") -> list[str]:
        # entities affected if this entity changes (outgoing edges)
        try:
            rels = await self._graph.list_relationships(entity_id) if hasattr(self._graph, "list_relationships") else []
        except Exception:
            rels = []
        return [r.target_entity_id for r in rels if r.source_entity_id == entity_id]

    async def affected_systems(self, entity_id: str, tenant_id: str = "default") -> list[str]:
        return await self.impact_analysis(entity_id, tenant_id)

    async def relationship_explanation(self, source_id: str, target_id: str) -> dict[str, Any]:
        paths = await self.path_discovery(source_id, target_id)
        return {"source": source_id, "target": target_id, "paths": paths[:5], "explanation": f"Path from {source_id} to {target_id} via {len(paths)} route(s)" if paths else "No path found"}
