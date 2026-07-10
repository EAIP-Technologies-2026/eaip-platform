from __future__ import annotations

import pytest

from eaip.kgraph.exceptions import GraphTraversalError
from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.models import Entity, Relationship


class TestGraphTraversal:
    @pytest.fixture
    async def graph(self) -> KnowledgeGraph:
        g = KnowledgeGraph()
        await g.add_entity(Entity(id="e1", type="person", name="Alice", properties={"city": "NYC"}))
        await g.add_entity(Entity(id="e2", type="person", name="Bob", properties={"city": "NYC"}))
        await g.add_entity(Entity(id="e3", type="person", name="Charlie", properties={"city": "LA"}))
        await g.add_entity(Entity(id="e4", type="org", name="ACME"))
        await g.add_entity(Entity(id="e5", type="org", name="Beta"))
        await g.add_relationship(Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2"))
        await g.add_relationship(Relationship(id="r2", type="knows", source_entity_id="e2", target_entity_id="e3"))
        await g.add_relationship(Relationship(id="r3", type="works_at", source_entity_id="e1", target_entity_id="e4"))
        await g.add_relationship(Relationship(id="r4", type="works_at", source_entity_id="e2", target_entity_id="e5"))
        await g.add_relationship(Relationship(id="r5", type="knows", source_entity_id="e3", target_entity_id="e1"))
        return g

    # ── BFS ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_bfs(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.bfs("e1", max_depth=2)
        assert len(result["entity_ids"]) >= 3

    @pytest.mark.asyncio
    async def test_bfs_max_depth(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.bfs("e1", max_depth=1)
        assert len(result["entity_ids"]) == 3  # e1 + immediate neighbors (e2, e4)

    @pytest.mark.asyncio
    async def test_bfs_start_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphTraversalError):
            await graph.traversal_service.bfs("nonexistent")

    @pytest.mark.asyncio
    async def test_bfs_with_predicate(self, graph: KnowledgeGraph) -> None:
        def pred(e: Entity, r: Relationship | None) -> bool:
            return e.type == "org"
        result = await graph.traversal_service.bfs("e1", max_depth=2, predicate=pred)
        assert len(result["entity_ids"]) == 2  # e1 + orgs

    @pytest.mark.asyncio
    async def test_bfs_with_rel_types(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.bfs("e1", max_depth=2, rel_types=("works_at",))
        assert len(result["entity_ids"]) == 2  # e1 + ACME only

    # ── DFS ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_dfs(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.dfs("e1", max_depth=3)
        assert len(result["entity_ids"]) >= 3

    @pytest.mark.asyncio
    async def test_dfs_max_depth(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.dfs("e1", max_depth=1)
        assert len(result["entity_ids"]) >= 2

    @pytest.mark.asyncio
    async def test_dfs_start_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphTraversalError):
            await graph.traversal_service.dfs("nonexistent")

    # ── Shortest Path ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_shortest_path(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.shortest_path("e1", "e3")
        assert len(result["paths"]) == 1
        # direct path e1->e3 via r5 due to bidirectional "both" traversal
        assert result["paths"][0]["length"] == 1

    @pytest.mark.asyncio
    async def test_shortest_path_same_node(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.shortest_path("e1", "e1")
        assert len(result["paths"]) == 1
        assert result["paths"][0]["length"] == 0

    @pytest.mark.asyncio
    async def test_shortest_path_no_path(self, graph: KnowledgeGraph) -> None:
        g = KnowledgeGraph()
        await g.add_entity(Entity(id="e1", type="person", name="Alice"))
        await g.add_entity(Entity(id="e2", type="person", name="Bob"))
        result = await g.traversal_service.shortest_path("e1", "e2")
        assert result["paths"] == []

    @pytest.mark.asyncio
    async def test_shortest_path_source_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphTraversalError):
            await graph.traversal_service.shortest_path("nonexistent", "e1")

    @pytest.mark.asyncio
    async def test_shortest_path_target_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphTraversalError):
            await graph.traversal_service.shortest_path("e1", "nonexistent")

    # ── Subgraph ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_subgraph(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.get_subgraph(["e1", "e4"])
        assert len(result["entity_ids"]) >= 2

    @pytest.mark.asyncio
    async def test_get_subgraph_depth(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.get_subgraph(["e1"], depth=1)
        assert len(result["entity_ids"]) >= 2

    @pytest.mark.asyncio
    async def test_get_subgraph_empty(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.get_subgraph([])
        assert result["entity_ids"] == []

    # ── Conditional paths ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_find_paths_with_condition(self, graph: KnowledgeGraph) -> None:
        paths = await graph.traversal_service.find_paths_with_condition("e1", "org")
        assert len(paths) >= 1
        assert all(p["entity_ids"][-1] in ("e4", "e5") for p in paths)

    # ── Cycle detection ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_detect_cycles(self, graph: KnowledgeGraph) -> None:
        cycles = await graph.traversal_service.detect_cycles("e1", max_depth=5)
        # e1 -> e2 -> e3 -> e1 is a cycle
        assert len(cycles) >= 1

    @pytest.mark.asyncio
    async def test_detect_cycles_no_cycle(self, graph: KnowledgeGraph) -> None:
        g = KnowledgeGraph()
        await g.add_entity(Entity(id="e1", type="person", name="Alice"))
        await g.add_entity(Entity(id="e2", type="person", name="Bob"))
        await g.add_relationship(Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2"))
        cycles = await g.traversal_service.detect_cycles("e1", max_depth=5)
        assert cycles == []

    @pytest.mark.asyncio
    async def test_detect_cycles_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphTraversalError):
            await graph.traversal_service.detect_cycles("nonexistent")

    # ── Centrality ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_compute_centrality(self, graph: KnowledgeGraph) -> None:
        result = await graph.traversal_service.compute_centrality("e1")
        assert result["entity_id"] == "e1"
        assert result["reachable_nodes"] > 0
        assert 0 <= result["centrality"] <= 1

    @pytest.mark.asyncio
    async def test_compute_centrality_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphTraversalError):
            await graph.traversal_service.compute_centrality("nonexistent")
