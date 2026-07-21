from __future__ import annotations

from eaip.kgraph.events import (
    EntityAdded,
    EntityDeleted,
    EntityUpdated,
    GraphEvent,
    GraphIndexRebuilt,
    GraphQueryExecuted,
    GraphTraversalExecuted,
    InferredRelationshipCreated,
    RelationshipAdded,
    RelationshipDeleted,
    RelationshipUpdated,
)


class TestGraphEvents:
    def test_entity_added(self) -> None:
        event = EntityAdded(entity_id="e1", entity_type="person", entity_name="Alice")
        assert event.event_type == "eaip.kgraph.entity.added"
        assert event.entity_id == "e1"
        assert event.entity_name == "Alice"

    def test_entity_updated(self) -> None:
        event = EntityUpdated(entity_id="e1", entity_type="person", changes={"name": "Alice B."})
        assert event.event_type == "eaip.kgraph.entity.updated"
        assert event.changes["name"] == "Alice B."

    def test_entity_deleted(self) -> None:
        event = EntityDeleted(entity_id="e1", entity_type="person", cascade=True)
        assert event.event_type == "eaip.kgraph.entity.deleted"
        assert event.cascade is True

    def test_entity_deleted_default_cascade(self) -> None:
        event = EntityDeleted(entity_id="e1", entity_type="person")
        assert event.cascade is False

    def test_relationship_added(self) -> None:
        event = RelationshipAdded(
            relationship_id="r1",
            relationship_type="knows",
            source_entity_id="e1",
            target_entity_id="e2",
        )
        assert event.event_type == "eaip.kgraph.relationship.added"
        assert event.source_entity_id == "e1"

    def test_relationship_updated(self) -> None:
        event = RelationshipUpdated(
            relationship_id="r1", relationship_type="knows", changes={"weight": 0.5}
        )
        assert event.event_type == "eaip.kgraph.relationship.updated"
        assert event.changes["weight"] == 0.5

    def test_relationship_deleted(self) -> None:
        event = RelationshipDeleted(relationship_id="r1", relationship_type="knows")
        assert event.event_type == "eaip.kgraph.relationship.deleted"

    def test_graph_query_executed(self) -> None:
        event = GraphQueryExecuted(query_mode="bfs", result_count=5, duration_ms=10.0)
        assert event.event_type == "eaip.kgraph.query.executed"
        assert event.query_mode == "bfs"

    def test_graph_traversal_executed(self) -> None:
        event = GraphTraversalExecuted(
            start_entity_id="e1", depth=3, direction="out", nodes_visited=4
        )
        assert event.event_type == "eaip.kgraph.traversal.executed"
        assert event.nodes_visited == 4

    def test_graph_index_rebuilt(self) -> None:
        event = GraphIndexRebuilt(entity_count=10, relationship_count=5)
        assert event.event_type == "eaip.kgraph.index.rebuilt"
        assert event.entity_count == 10

    def test_inferred_relationship_created(self) -> None:
        event = InferredRelationshipCreated(
            source_entity_id="e1",
            target_entity_id="e3",
            relationship_type="shared_property",
            confidence=0.75,
        )
        assert event.event_type == "eaip.kgraph.inferred_relationship.created"
        assert event.confidence == 0.75

    def test_base_event_type(self) -> None:
        assert GraphEvent.event_type == "eaip.kgraph.event"

    def test_entity_added_immutable(self) -> None:
        event = EntityAdded(entity_id="e1", entity_type="person", entity_name="Alice")
        try:
            event.entity_id = "e2"
            raise AssertionError()
        except (TypeError, ValueError):
            pass
