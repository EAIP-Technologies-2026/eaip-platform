"""Strategy-to-Execution Graph — links objectives → initiatives → missions → workflows → outcomes."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.logging.context import get_logger


class StrategyExecutionGraph:
    """Connects strategic objectives to operational execution via the knowledge graph.

    Edges: objective → initiative → mission → workflow → outcome
    Uses in-memory adjacency when kgraph is not wired.
    """

    def __init__(self, kgraph: Any = None) -> None:
        self._kgraph = kgraph
        self._log = get_logger("eaip.strategy.graph")
        # fallback adjacency: {source_id: [(edge_id, target_id, edge_type)]}
        self._edges: dict[str, list[tuple[str, str, str]]] = {}

    def _add_edge(self, source_id: str, target_id: str, edge_type: str) -> str:
        edge_id = f"edge-{uuid.uuid4().hex[:8]}"
        self._edges.setdefault(source_id, []).append((edge_id, target_id, edge_type))
        self._edges.setdefault(target_id, [])
        return edge_id

    async def connect_objective_to_initiative(self, objective_id: str, initiative_id: str) -> str:
        edge_id = self._add_edge(objective_id, initiative_id, "objective_to_initiative")
        self._log.debug("graph.edge.added", source=objective_id, target=initiative_id, type="objective_to_initiative")
        return edge_id

    async def connect_initiative_to_mission(self, initiative_id: str, mission_id: str) -> str:
        edge_id = self._add_edge(initiative_id, mission_id, "initiative_to_mission")
        self._log.debug("graph.edge.added", source=initiative_id, target=mission_id, type="initiative_to_mission")
        return edge_id

    async def connect_mission_to_workflow(self, mission_id: str, workflow_id: str) -> str:
        edge_id = self._add_edge(mission_id, workflow_id, "mission_to_workflow")
        self._log.debug("graph.edge.added", source=mission_id, target=workflow_id, type="mission_to_workflow")
        return edge_id

    async def connect_workflow_to_outcome(self, workflow_id: str, outcome_id: str) -> str:
        edge_id = self._add_edge(workflow_id, outcome_id, "workflow_to_outcome")
        self._log.debug("graph.edge.added", source=workflow_id, target=outcome_id, type="workflow_to_outcome")
        return edge_id

    async def trace_objective_to_outcomes(self, objective_id: str) -> list[dict[str, Any]]:
        """Trace the full chain from an objective to all downstream outcomes."""
        chain: list[dict[str, Any]] = []
        visited: set[str] = set()
        queue: list[str] = [objective_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for edge_id, target_id, edge_type in self._edges.get(current, []):
                chain.append({"source": current, "target": target_id, "edge_type": edge_type, "edge_id": edge_id})
                queue.append(target_id)
        return chain

    async def get_strategy_graph(self, tenant_id: str) -> dict[str, Any]:
        """Return a bounded subgraph of all strategy edges."""
        all_edges: list[dict[str, Any]] = []
        for source, targets in self._edges.items():
            for edge_id, target_id, edge_type in targets:
                all_edges.append({"source": source, "target": target_id, "edge_type": edge_type, "edge_id": edge_id})
        nodes: set[str] = set()
        for e in all_edges:
            nodes.add(e["source"])
            nodes.add(e["target"])
        return {"tenant_id": tenant_id, "nodes": list(nodes), "edges": all_edges, "node_count": len(nodes), "edge_count": len(all_edges)}

    async def get_downstream(self, node_id: str) -> list[str]:
        """Get immediate downstream nodes."""
        return [target_id for _, target_id, _ in self._edges.get(node_id, [])]

    async def get_upstream(self, node_id: str) -> list[str]:
        """Get immediate upstream nodes."""
        upstream: list[str] = []
        for source, targets in self._edges.items():
            for _, target_id, _ in targets:
                if target_id == node_id:
                    upstream.append(source)
        return upstream


__all__ = ["StrategyExecutionGraph"]
