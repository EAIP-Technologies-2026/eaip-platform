from __future__ import annotations

import pytest

from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.index import GraphIndex
from eaip.kgraph.models import Entity, Relationship


class TestGraphIndex:
    @pytest.fixture
    async def graph_and_index(self) -> tuple[KnowledgeGraph, GraphIndex]:
        g = KnowledgeGraph()
        idx = GraphIndex(g)
        return g, idx

    @pytest.mark.asyncio
    async def test_index_entity(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        e = Entity(id="e1", type="person", name="Alice", source="manual", properties={"city": "NYC"})
        await g.add_entity(e)
        await idx.index_entity(e)
        results = await idx.search_entities("Alice")
        assert len(results) == 1
        assert results[0].id == "e1"

    @pytest.mark.asyncio
    async def test_index_entity_by_type(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        e = Entity(id="e1", type="person", name="Alice")
        await g.add_entity(e)
        await idx.index_entity(e)
        results = await idx.search_entities("person")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_index_entity_by_property(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        e = Entity(id="e1", type="person", name="Alice", properties={"city": "NYC", "role": "engineer"})
        await g.add_entity(e)
        await idx.index_entity(e)
        results = await idx.search_entities("nyc")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_index_entity_filtered_by_type(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        await g.add_entity(Entity(id="e1", type="person", name="Alice"))
        await g.add_entity(Entity(id="e2", type="org", name="Alice Corp"))
        for eid in ("e1", "e2"):
            await idx.index_entity(g.entities[eid])
        results = await idx.search_entities("Alice", entity_type="person")
        assert len(results) == 1
        assert results[0].id == "e1"

    @pytest.mark.asyncio
    async def test_search_no_results(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        _, idx = graph_and_index
        results = await idx.search_entities("nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_index_relationship(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        await g.add_entity(Entity(id="e1", type="person", name="Alice"))
        await g.add_entity(Entity(id="e2", type="person", name="Bob"))
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        await g.add_relationship(r)
        await idx.index_relationship(r)
        results = await idx.search_relationships("knows")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_relationships_all(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        await g.add_entity(Entity(id="e1", type="person", name="Alice"))
        await g.add_entity(Entity(id="e2", type="person", name="Bob"))
        await g.add_entity(Entity(id="e3", type="person", name="Charlie"))
        r1 = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        r2 = Relationship(id="r2", type="knows", source_entity_id="e2", target_entity_id="e3")
        await g.add_relationship(r1)
        await g.add_relationship(r2)
        await idx.index_relationship(r1)
        await idx.index_relationship(r2)
        results = await idx.search_relationships()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_rebuild_index(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        await g.add_entity(Entity(id="e1", type="person", name="Alice"))
        await g.add_entity(Entity(id="e2", type="person", name="Bob"))
        await g.add_relationship(Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2"))
        await idx.rebuild_index()
        results = await idx.search_entities("Alice")
        assert len(results) == 1
        rel_results = await idx.search_relationships("knows")
        assert len(rel_results) == 1

    @pytest.mark.asyncio
    async def test_clear_index(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        e = Entity(id="e1", type="person", name="Alice")
        await g.add_entity(e)
        await idx.index_entity(e)
        await idx.clear_index()
        results = await idx.search_entities("Alice")
        assert results == []

    @pytest.mark.asyncio
    async def test_inspect_indices(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        g, idx = graph_and_index
        e = Entity(id="e1", type="person", name="Alice")
        await g.add_entity(e)
        await idx.index_entity(e)
        indices = idx.entity_indices
        assert len(indices) >= 1

    @pytest.mark.asyncio
    async def test_relationship_type_index_empty(self, graph_and_index: tuple[KnowledgeGraph, GraphIndex]) -> None:
        _, idx = graph_and_index
        assert idx.relationship_type_index == {}
