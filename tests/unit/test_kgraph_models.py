from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from eaip.kgraph.models import (
    Entity,
    EntityIndex,
    GraphConfig,
    GraphQuery,
    GraphQueryMode,
    GraphResult,
    GraphStats,
    Path,
    PersistenceType,
    Relationship,
)


class TestEntityModel:
    def test_entity_defaults(self) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        assert e.id == "e1"
        assert e.type == "person"
        assert e.name == "Alice"
        assert e.description == ""
        assert e.properties == {}
        assert e.confidence == 1.0
        assert e.tags == ()
        assert e.source == ""

    def test_entity_with_all_fields(self) -> None:
        e = Entity(
            id="e2",
            type="org",
            name="ACME",
            description="A company",
            properties={"founded": 1999},
            source="import",
            confidence=0.85,
            metadata={"source_file": "data.json"},
            tags=("tech", "enterprise"),
        )
        assert e.description == "A company"
        assert e.properties == {"founded": 1999}
        assert e.confidence == 0.85
        assert e.metadata == {"source_file": "data.json"}
        assert e.tags == ("tech", "enterprise")

    def test_entity_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Entity(id="e3", type="test", name="Bad", confidence=1.5)
        with pytest.raises(ValidationError):
            Entity(id="e4", type="test", name="Bad", confidence=-0.1)

    def test_entity_is_frozen(self) -> None:
        e = Entity(id="e5", type="t", name="N")
        with pytest.raises(ValidationError):
            e.name = "New"

    def test_entity_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Entity(id="e6", type="t", name="N", extra_field="x")  # type: ignore[call-arg]

    def test_entity_timestamps(self) -> None:
        e = Entity(id="e7", type="t", name="N")
        assert isinstance(e.created_at, datetime)
        assert isinstance(e.updated_at, datetime)
        assert e.created_at.tzinfo is not None

    def test_entity_empty_tags(self) -> None:
        e = Entity(id="e8", type="t", name="N", tags=())
        assert e.tags == ()


class TestRelationshipModel:
    def test_relationship_defaults(self) -> None:
        r = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        assert r.id == "r1"
        assert r.type == "knows"
        assert r.weight == 1.0
        assert r.bidirectional is False
        assert r.properties == {}

    def test_relationship_with_all_fields(self) -> None:
        r = Relationship(
            id="r2",
            type="works_at",
            source_entity_id="e1",
            target_entity_id="e2",
            properties={"since": 2020},
            weight=0.9,
            bidirectional=True,
            metadata={"verified": True},
        )
        assert r.weight == 0.9
        assert r.bidirectional is True
        assert r.metadata == {"verified": True}

    def test_relationship_weight_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Relationship(
                id="r3", type="t", source_entity_id="e1", target_entity_id="e2", weight=1.1
            )
        with pytest.raises(ValidationError):
            Relationship(
                id="r4", type="t", source_entity_id="e1", target_entity_id="e2", weight=-0.1
            )

    def test_relationship_is_frozen(self) -> None:
        r = Relationship(id="r5", type="t", source_entity_id="e1", target_entity_id="e2")
        with pytest.raises(ValidationError):
            r.type = "new"

    def test_relationship_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Relationship(id="r6", type="t", source_entity_id="e1", target_entity_id="e2", extra="x")  # type: ignore[call-arg]

    def test_relationship_self_reference(self) -> None:
        r = Relationship(id="r7", type="self", source_entity_id="e1", target_entity_id="e1")
        assert r.source_entity_id == r.target_entity_id


class TestGraphQueryModel:
    def test_graph_query_defaults(self) -> None:
        q = GraphQuery()
        assert q.query == ""
        assert q.max_depth == 3
        assert q.min_confidence == 0.0
        assert q.limit == 100
        assert q.mode is GraphQueryMode.BFS

    def test_graph_query_custom(self) -> None:
        q = GraphQuery(
            query="find related",
            entity_types=("person",),
            relationship_types=("knows",),
            max_depth=5,
            min_confidence=0.5,
            limit=50,
            filters={"region": "US"},
            mode=GraphQueryMode.SHORTEST_PATH,
            start_entity_id="e1",
        )
        assert q.max_depth == 5
        assert q.min_confidence == 0.5
        assert q.mode is GraphQueryMode.SHORTEST_PATH
        assert q.start_entity_id == "e1"

    def test_graph_query_depth_bounds(self) -> None:
        with pytest.raises(ValidationError):
            GraphQuery(max_depth=-1)

    def test_graph_query_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            GraphQuery(limit=-5)


class TestPathModel:
    def test_path_defaults(self) -> None:
        p = Path()
        assert p.entity_ids == ()
        assert p.relationship_ids == ()
        assert p.total_weight == 0.0
        assert p.length == 0

    def test_path_custom(self) -> None:
        p = Path(
            entity_ids=("e1", "e2", "e3"),
            relationship_ids=("r1", "r2"),
            total_weight=1.5,
            length=2,
        )
        assert p.entity_ids == ("e1", "e2", "e3")
        assert p.length == 2


class TestGraphResultModel:
    def test_graph_result_defaults(self) -> None:
        r = GraphResult()
        assert r.entities == ()
        assert r.relationships == ()
        assert r.paths == ()
        assert r.total_count == 0
        assert r.duration_ms == 0.0

    def test_graph_result_with_data(self) -> None:
        e = Entity(id="e1", type="person", name="Alice")
        rel = Relationship(id="r1", type="knows", source_entity_id="e1", target_entity_id="e2")
        p = Path(entity_ids=("e1", "e2"), relationship_ids=("r1",), length=1)
        r = GraphResult(
            entities=(e,),
            relationships=(rel,),
            paths=(p,),
            total_count=2,
            duration_ms=10.5,
        )
        assert len(r.entities) == 1
        assert len(r.paths) == 1
        assert r.duration_ms == 10.5


class TestGraphConfigModel:
    def test_graph_config_defaults(self) -> None:
        c = GraphConfig()
        assert c.enable_indexing is True
        assert c.max_traversal_depth == 10
        assert c.cache_enabled is True
        assert c.persistence_type is PersistenceType.MEMORY

    def test_graph_config_custom(self) -> None:
        c = GraphConfig(
            enable_indexing=False,
            index_entity_types=("person",),
            max_traversal_depth=20,
            cache_enabled=False,
            cache_ttl_seconds=600,
            persistence_type=PersistenceType.DATABASE,
        )
        assert c.enable_indexing is False
        assert c.index_entity_types == ("person",)
        assert c.persistence_type is PersistenceType.DATABASE

    def test_graph_config_depth_bounds(self) -> None:
        with pytest.raises(ValidationError):
            GraphConfig(max_traversal_depth=-1)


class TestEntityIndexModel:
    def test_entity_index_defaults(self) -> None:
        idx = EntityIndex(entity_type="person", field="name")
        assert idx.values == {}

    def test_entity_index_with_values(self) -> None:
        idx = EntityIndex(
            entity_type="person",
            field="name",
            values={"alice": ["e1", "e2"]},
        )
        assert idx.values["alice"] == ["e1", "e2"]


class TestGraphStatsModel:
    def test_graph_stats_defaults(self) -> None:
        s = GraphStats()
        assert s.total_entities == 0
        assert s.total_relationships == 0
        assert s.avg_degree == 0.0
        assert s.density == 0.0

    def test_graph_stats_custom(self) -> None:
        s = GraphStats(
            total_entities=10,
            total_relationships=15,
            entity_type_counts={"person": 6, "org": 4},
            relationship_type_counts={"knows": 10, "works_at": 5},
            avg_degree=3.0,
            density=0.1667,
        )
        assert s.total_entities == 10
        assert s.avg_degree == 3.0
        assert s.entity_type_counts["person"] == 6
        assert s.relationship_type_counts["knows"] == 10
