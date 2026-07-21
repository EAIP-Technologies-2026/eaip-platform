"""Tests for ProjectionBuilder."""

from __future__ import annotations

import pytest

from eaip.eventsourcing.exceptions import ProjectionNotFoundError
from eaip.eventsourcing.models import ProjectionConfig, ProjectionStatus, StoredEvent
from eaip.eventsourcing.projections import ProjectionBuilder


class TestProjectionBuilder:
    @pytest.fixture
    def builder(self) -> ProjectionBuilder:
        return ProjectionBuilder()

    @pytest.fixture
    def sample_event(self) -> StoredEvent:
        return StoredEvent(
            id="e1", aggregate_type="order", aggregate_id="123", event_type="order.created"
        )

    async def test_register_projection(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            state["count"] = state.get("count", 0) + 1
            return state

        proj = builder.register_projection("p1", "OrderCount", handler)
        assert proj.id == "p1"
        assert proj.name == "OrderCount"
        assert proj.status == ProjectionStatus.ACTIVE

    async def test_register_with_aggregate_types(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            return state

        proj = builder.register_projection("p1", "OrderCount", handler, aggregate_types=("order",))
        assert proj.aggregate_types == ("order",)

    async def test_unregister_projection(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            return state

        builder.register_projection("p1", "Test", handler)
        builder.unregister_projection("p1")
        with pytest.raises(ProjectionNotFoundError):
            builder.get_projection("p1")

    async def test_unregister_nonexistent(self, builder: ProjectionBuilder) -> None:
        with pytest.raises(ProjectionNotFoundError):
            builder.unregister_projection("nope")

    async def test_get_projection(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            return state

        builder.register_projection("p1", "Test", handler)
        proj = builder.get_projection("p1")
        assert proj.id == "p1"

    async def test_get_nonexistent(self, builder: ProjectionBuilder) -> None:
        with pytest.raises(ProjectionNotFoundError):
            builder.get_projection("nope")

    async def test_list_projections(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            return state

        assert builder.list_projections() == []
        builder.register_projection("p1", "A", handler)
        builder.register_projection("p2", "B", handler)
        assert len(builder.list_projections()) == 2

    async def test_build_projection(self, builder: ProjectionBuilder) -> None:
        async def count_handler(event: StoredEvent, state: dict) -> dict:
            state["count"] = state.get("count", 0) + 1
            return state

        builder.register_projection("p1", "Counter", count_handler)
        events = [
            StoredEvent(
                id="e1", aggregate_type="order", aggregate_id="1", event_type="order.created"
            ),
            StoredEvent(
                id="e2", aggregate_type="order", aggregate_id="1", event_type="order.shipped"
            ),
        ]
        proj = await builder.build_projection("p1", events)
        assert proj.state == {"count": 2}
        assert proj.last_processed_event_id == "e2"

    async def test_build_projection_no_handler(self, builder: ProjectionBuilder) -> None:
        with pytest.raises(ProjectionNotFoundError):
            await builder.build_projection("nope", [])

    async def test_build_projection_handler_error(self, builder: ProjectionBuilder) -> None:
        async def failing_handler(event: StoredEvent, state: dict) -> dict:
            raise ValueError("handler error")

        builder.register_projection("p1", "Failing", failing_handler)
        events = [
            StoredEvent(
                id="e1", aggregate_type="order", aggregate_id="1", event_type="order.created"
            )
        ]
        with pytest.raises(ValueError):
            await builder.build_projection("p1", events)

        proj = builder.get_projection("p1")
        assert proj.status == ProjectionStatus.FAILED

    async def test_rebuild_all(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            state["count"] = state.get("count", 0) + 1
            return state

        builder.register_projection("p1", "A", handler)
        builder.register_projection("p2", "B", handler)
        e1 = StoredEvent(
            id="e1", aggregate_type="order", aggregate_id="1", event_type="order.created"
        )
        e2 = StoredEvent(
            id="e2", aggregate_type="order", aggregate_id="1", event_type="order.shipped"
        )
        results = await builder.rebuild_all({"p1": [e1, e2], "p2": [e1]})
        assert len(results) == 2

    async def test_process_event(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            state["events"] = [*state.get("events", []), event.event_type]
            return state

        builder.register_projection("p1", "Logger", handler, aggregate_types=("order",))
        event = StoredEvent(
            id="e1", aggregate_type="order", aggregate_id="1", event_type="order.created"
        )
        updated = await builder.process_event(event)
        assert len(updated) == 1
        assert updated[0].state == {"events": ["order.created"]}

    async def test_process_event_skips_non_matching_aggregate_type(
        self, builder: ProjectionBuilder
    ) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            state["seen"] = True
            return state

        builder.register_projection("p1", "OnlyOrder", handler, aggregate_types=("order",))
        event = StoredEvent(
            id="e1", aggregate_type="invoice", aggregate_id="1", event_type="invoice.paid"
        )
        updated = await builder.process_event(event)
        assert updated == []

    async def test_process_event_skips_paused(self, builder: ProjectionBuilder) -> None:
        async def handler(event: StoredEvent, state: dict) -> dict:
            state["seen"] = True
            return state

        builder.register_projection("p1", "Paused", handler)
        paused = builder.get_projection("p1").model_copy(update={"status": ProjectionStatus.PAUSED})
        builder._projections["p1"] = paused
        event = StoredEvent(
            id="e1", aggregate_type="order", aggregate_id="1", event_type="order.created"
        )
        updated = await builder.process_event(event)
        assert updated == []

    async def test_config_property(self, builder: ProjectionBuilder) -> None:
        assert isinstance(builder.config, ProjectionConfig)

    async def test_custom_config(self) -> None:
        config = ProjectionConfig(batch_size=10, max_retries=1)
        builder = ProjectionBuilder(config=config)
        assert builder.config.batch_size == 10
        assert builder.config.max_retries == 1
