from __future__ import annotations

import pytest

from eaip.kgraph.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    GraphQueryError,
    RelationshipNotFoundError,
)
from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.models import (
    Entity,
    GraphQuery,
    GraphQueryMode,
    Relationship,
)


class TestKnowledgeGraph:
    @pytest.fixture
    def graph(self) -> KnowledgeGraph:
        return KnowledgeGraph()

    @pytest.fixture
    async def populated_graph(self) -> KnowledgeGraph:
        g = KnowledgeGraph()
        await g.add_entity(Entity(id="e1", type="person", name="Alice"))
        await g.add_entity(Entity(id="e2", type="person", name="Bob"))
        await g.add_entity(Entity(id="e3", type="person", name="Charlie"))
        await g.add_entity(Entity(id="e4", type="org", name="ACME"))
        await g.add_relationship(
            Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        )
        await g.add_relationship(
            Relationship(id="r2", type="knows", source_entity_id="e2", target_entity_id="e3")
        )
        await g.add_relationship(
            Relationship(id="r3", type="works_at", source_entity_id="e1", target_entity_id="e4")
        )
        return g

    # ── Entity CRUD ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_add_entity(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        result = await graph.add_entity(e)
        assert result.id == "e1"
        assert result.name == "Alice"

    @pytest.mark.asyncio
    async def test_add_entity_duplicate(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        await graph.add_entity(e)
        with pytest.raises(EntityValidationError):
            await graph.add_entity(e)

    @pytest.mark.asyncio
    async def test_add_entity_empty_id(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(EntityValidationError):
            await graph.add_entity(Entity(id="", type="person", name="N"))

    @pytest.mark.asyncio
    async def test_add_entity_empty_type(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(EntityValidationError):
            await graph.add_entity(Entity(id="e1", type="", name="N"))

    @pytest.mark.asyncio
    async def test_get_entity(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        await graph.add_entity(e)
        result = await graph.get_entity("e1")
        assert result.name == "Alice"

    @pytest.mark.asyncio
    async def test_get_entity_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(EntityNotFoundError):
            await graph.get_entity("nonexistent")

    @pytest.mark.asyncio
    async def test_update_entity(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        await graph.add_entity(e)
        updated = await graph.update_entity("e1", {"name": "Alice B.", "description": "Updated"})
        assert updated.name == "Alice B."
        assert updated.description == "Updated"

    @pytest.mark.asyncio
    async def test_update_entity_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(EntityNotFoundError):
            await graph.update_entity("nonexistent", {"name": "X"})

    @pytest.mark.asyncio
    async def test_update_entity_invalid_field(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        await graph.add_entity(e)
        with pytest.raises(EntityValidationError):
            await graph.update_entity("e1", {"invalid_field": "value"})

    @pytest.mark.asyncio
    async def test_update_entity_merges_properties(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice", properties={"age": 30})
        await graph.add_entity(e)
        updated = await graph.update_entity("e1", {"properties": {"city": "NYC"}})
        assert updated.properties["age"] == 30
        assert updated.properties["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_delete_entity(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        await graph.add_entity(e)
        await graph.delete_entity("e1")
        with pytest.raises(EntityNotFoundError):
            await graph.get_entity("e1")

    @pytest.mark.asyncio
    async def test_delete_entity_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(EntityNotFoundError):
            await graph.delete_entity("nonexistent")

    @pytest.mark.asyncio
    async def test_delete_entity_with_relationships_no_cascade(self, graph: KnowledgeGraph) -> None:
        g = KnowledgeGraph()
        e1 = Entity(id="e1", type="person", name="Alice")
        e2 = Entity(id="e2", type="person", name="Bob")
        await g.add_entity(e1)
        await g.add_entity(e2)
        await g.add_relationship(
            Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        )
        with pytest.raises(EntityValidationError):
            await g.delete_entity("e1", cascade=False)

    @pytest.mark.asyncio
    async def test_delete_entity_cascade(self, graph: KnowledgeGraph) -> None:
        g = KnowledgeGraph()
        e1 = Entity(id="e1", type="person", name="Alice")
        e2 = Entity(id="e2", type="person", name="Bob")
        await g.add_entity(e1)
        await g.add_entity(e2)
        await g.add_relationship(
            Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        )
        await g.delete_entity("e1", cascade=True)
        with pytest.raises(RelationshipNotFoundError):
            await g.get_relationship("r1")

    # ── Relationship CRUD ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_add_relationship(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        result = await graph.add_relationship(r)
        assert result.id == "r1"

    @pytest.mark.asyncio
    async def test_add_relationship_missing_source(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        with pytest.raises(EntityNotFoundError):
            await graph.add_relationship(r)

    @pytest.mark.asyncio
    async def test_add_relationship_missing_target(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        with pytest.raises(EntityNotFoundError):
            await graph.add_relationship(r)

    @pytest.mark.asyncio
    async def test_add_relationship_duplicate(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        await graph.add_relationship(r)
        with pytest.raises(EntityValidationError):
            await graph.add_relationship(r)

    @pytest.mark.asyncio
    async def test_get_relationship(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        await graph.add_relationship(r)
        result = await graph.get_relationship("r1")
        assert result.type == "knows"

    @pytest.mark.asyncio
    async def test_get_relationship_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(RelationshipNotFoundError):
            await graph.get_relationship("nonexistent")

    @pytest.mark.asyncio
    async def test_update_relationship(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        await graph.add_relationship(r)
        updated = await graph.update_relationship("r1", {"weight": 0.5})
        assert updated.weight == 0.5

    @pytest.mark.asyncio
    async def test_delete_relationship(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        await graph.add_relationship(r)
        await graph.delete_relationship("r1")
        with pytest.raises(RelationshipNotFoundError):
            await graph.get_relationship("r1")

    @pytest.mark.asyncio
    async def test_delete_relationship_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(RelationshipNotFoundError):
            await graph.delete_relationship("nonexistent")

    # ── Self-relationship ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_self_relationship(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        r = Relationship(id="r1", type="self", source_entity_id="e1", target_entity_id="e1")
        result = await graph.add_relationship(r)
        assert result.id == "r1"
        neighbors = await graph.get_neighbors("e1")
        assert len(neighbors) == 1

    # ── Queries ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_query_bfs(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        q = GraphQuery(mode=GraphQueryMode.BFS, start_entity_id="e1", max_depth=3)
        result = await g.query(q)
        assert result.total_count >= 3

    @pytest.mark.asyncio
    async def test_query_bfs_no_start_id(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphQueryError):
            await graph.query(GraphQuery(mode=GraphQueryMode.BFS))

    @pytest.mark.asyncio
    async def test_query_dfs(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        q = GraphQuery(mode=GraphQueryMode.DFS, start_entity_id="e1", max_depth=3)
        result = await g.query(q)
        assert result.total_count >= 3

    @pytest.mark.asyncio
    async def test_query_shortest_path(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        q = GraphQuery(
            mode=GraphQueryMode.SHORTEST_PATH,
            start_entity_id="e1",
            filters={"target_entity_id": "e3"},
        )
        result = await g.query(q)
        assert result.total_count >= 2

    @pytest.mark.asyncio
    async def test_query_shortest_path_no_target(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphQueryError):
            await graph.query(GraphQuery(mode=GraphQueryMode.SHORTEST_PATH, start_entity_id="e1"))

    @pytest.mark.asyncio
    async def test_query_subgraph(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        q = GraphQuery(
            mode=GraphQueryMode.SUBGRAPH,
            filters={"entity_ids": ["e1", "e4"]},
            max_depth=1,
        )
        result = await g.query(q)
        assert result.total_count >= 2

    @pytest.mark.asyncio
    async def test_query_subgraph_no_entity_ids(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(GraphQueryError):
            await graph.query(GraphQuery(mode=GraphQueryMode.SUBGRAPH))

    # ── Traversal wrappers ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_traverse(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        result = await g.traverse("e1", depth=2)
        assert len(result["entity_ids"]) >= 2

    @pytest.mark.asyncio
    async def test_get_neighbors(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        neighbors = await g.get_neighbors("e1")
        assert len(neighbors) == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_filtered(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        neighbors = await g.get_neighbors("e1", rel_types=("knows",))
        assert len(neighbors) == 1
        assert neighbors[0].name == "Bob"

    @pytest.mark.asyncio
    async def test_get_neighbors_not_found(self, graph: KnowledgeGraph) -> None:
        with pytest.raises(EntityNotFoundError):
            await graph.get_neighbors("nonexistent")

    @pytest.mark.asyncio
    async def test_shortest_path(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        path = await g.get_shortest_path("e1", "e3")
        assert path is not None
        assert path.length == 2

    @pytest.mark.asyncio
    async def test_shortest_path_none(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        path = await graph.get_shortest_path("e1", "e2")
        assert path is None

    @pytest.mark.asyncio
    async def test_shortest_path_no_connection(self, graph: KnowledgeGraph) -> None:
        await graph.add_entity(Entity(id="e1", type="person", name="Alice"))
        await graph.add_entity(Entity(id="e2", type="person", name="Bob"))
        path = await graph.get_shortest_path("e1", "e2")
        assert path is None

    # ── Entity search ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_find_entities_by_type(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        persons = await g.find_entities_by_type("person")
        assert len(persons) == 3
        orgs = await g.find_entities_by_type("org")
        assert len(orgs) == 1

    @pytest.mark.asyncio
    async def test_find_entities_by_property(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice", properties={"city": "NYC"})
        await graph.add_entity(e)
        results = await graph.find_entities_by_property("city", "NYC")
        assert len(results) == 1
        assert results[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_find_entities_by_property_no_match(self, graph: KnowledgeGraph) -> None:
        e = Entity(id="e1", type="person", name="Alice", properties={"city": "NYC"})
        await graph.add_entity(e)
        results = await graph.find_entities_by_property("city", "LA")
        assert results == []

    # ── Empty graph ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_empty_graph_stats(self, graph: KnowledgeGraph) -> None:
        stats = await graph.get_stats()
        assert stats.total_entities == 0
        assert stats.total_relationships == 0
        assert stats.avg_degree == 0.0

    @pytest.mark.asyncio
    async def test_empty_graph_find_by_type(self, graph: KnowledgeGraph) -> None:
        results = await graph.find_entities_by_type("person")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_subgraph(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        result = await g.get_subgraph(["e1"])
        assert "entity_ids" in result
        assert len(result["entity_ids"]) >= 1

    # ── Stats ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_graph_stats(self, populated_graph: KnowledgeGraph) -> None:
        g = populated_graph
        stats = await g.get_stats()
        assert stats.total_entities == 4
        assert stats.total_relationships == 3
        assert stats.entity_type_counts["person"] == 3
        assert stats.entity_type_counts["org"] == 1
