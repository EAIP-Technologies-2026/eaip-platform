from __future__ import annotations

import pytest

from eaip.kgraph.exceptions import EntityNotFoundError
from eaip.kgraph.graph import KnowledgeGraph
from eaip.kgraph.models import Entity, Relationship
from eaip.kgraph.semantic import SemanticRelationshipService


class TestSemanticRelationshipService:
    @pytest.fixture
    async def graph_and_service(self) -> tuple[KnowledgeGraph, SemanticRelationshipService]:
        g = KnowledgeGraph()
        await g.add_entity(
            Entity(
                id="e1",
                type="person",
                name="Alice",
                properties={"city": "NYC", "dept": "eng"},
                tags=("python", "ml"),
            )
        )
        await g.add_entity(
            Entity(
                id="e2",
                type="person",
                name="Bob",
                properties={"city": "NYC", "dept": "eng"},
                tags=("python", "backend"),
            )
        )
        await g.add_entity(
            Entity(
                id="e3",
                type="person",
                name="Charlie",
                properties={"city": "LA", "dept": "sales"},
                tags=("sales",),
            )
        )
        await g.add_entity(
            Entity(id="e4", type="org", name="ACME", properties={"industry": "tech"})
        )
        await g.add_entity(
            Entity(
                id="e5",
                type="person",
                name="Diana",
                properties={"city": "NYC", "dept": "eng"},
                tags=("python", "ml"),
            )
        )
        await g.add_relationship(
            Relationship(
                id="r1",
                type="knows",
                source_entity_id="e1",
                target_entity_id="e2",
            )
        )
        service = SemanticRelationshipService(g)
        return g, service

    # ── Infer relationships ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_infer_relationships(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _g, svc = graph_and_service
        inferred = await svc.infer_relationships("e1", max_distance=1)
        assert len(inferred) >= 1
        assert any(i["target_entity_id"] == "e2" for i in inferred)

    @pytest.mark.asyncio
    async def test_infer_relationships_not_found(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        with pytest.raises(EntityNotFoundError):
            await svc.infer_relationships("nonexistent")

    @pytest.mark.asyncio
    async def test_infer_relationships_no_shared(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        inferred = await svc.infer_relationships("e4", max_distance=1)
        assert inferred == []

    # ── Similarity ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_compute_similarity_high(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        sim = await svc.compute_similarity("e1", "e2")
        assert sim > 0  # share city, dept, python tag

    @pytest.mark.asyncio
    async def test_compute_similarity_low(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        sim = await svc.compute_similarity("e1", "e3")
        assert sim == 0  # no shared tags/properties

    @pytest.mark.asyncio
    async def test_compute_similarity_same(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        sim = await svc.compute_similarity("e1", "e1")
        assert sim == 1.0

    @pytest.mark.asyncio
    async def test_compute_similarity_not_found(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        with pytest.raises(EntityNotFoundError):
            await svc.compute_similarity("e1", "nonexistent")

    # ── Find similar ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_find_similar_entities(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        results = await svc.find_similar_entities("e1", threshold=0.1)
        assert len(results) >= 2  # e5 (1.0) and e2 (0.6)
        assert results[0]["entity_id"] == "e5"

    @pytest.mark.asyncio
    async def test_find_similar_entities_high_threshold(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        results = await svc.find_similar_entities("e1", threshold=0.95)
        assert len(results) == 1
        assert results[0]["entity_id"] == "e5"

    @pytest.mark.asyncio
    async def test_find_similar_not_found(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        with pytest.raises(EntityNotFoundError):
            await svc.find_similar_entities("nonexistent")

    # ── Clustering ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_entity_cluster(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        clusters = await svc.get_entity_cluster("person", min_connections=2)
        assert len(clusters) >= 1

    @pytest.mark.asyncio
    async def test_get_entity_cluster_no_type(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        clusters = await svc.get_entity_cluster("nonexistent")
        assert clusters == []

    # ── Suggestions ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_suggest_relationships(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        suggestions = await svc.suggest_relationships("e1")
        assert len(suggestions) >= 1

    @pytest.mark.asyncio
    async def test_suggest_relationships_not_found(
        self, graph_and_service: tuple[KnowledgeGraph, SemanticRelationshipService]
    ) -> None:
        _, svc = graph_and_service
        with pytest.raises(EntityNotFoundError):
            await svc.suggest_relationships("nonexistent")
