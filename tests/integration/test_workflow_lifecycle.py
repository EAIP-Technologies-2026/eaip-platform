"""Integration tests for workflow lifecycle management.

Covers CRUD, versioning, archiving, event publishing, and isolation.
"""

from __future__ import annotations

import pytest

from eaip.events.bus import EventBus
from eaip.workflow.events import WorkflowArchived, WorkflowCreated, WorkflowUpdated
from eaip.workflow.exceptions import WorkflowNotFoundError
from eaip.workflow.models import WorkflowDefinition, WorkflowStatus
from eaip.workflow.registry import WorkflowRegistry


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def registry(event_bus: EventBus) -> WorkflowRegistry:
    return WorkflowRegistry(event_bus=event_bus)


@pytest.fixture
def sample_def() -> WorkflowDefinition:
    return WorkflowDefinition(id="wf-1", name="Test Workflow", version="1.0.0")


class TestWorkflowRegistry:
    """Workflow definition CRUD."""

    async def test_create(self, registry: WorkflowRegistry) -> None:
        wf = WorkflowDefinition(id="w1", name="Workflow One")
        created = await registry.create(wf)
        assert created.id == "w1"
        assert created.name == "Workflow One"
        fetched = await registry.get("w1")
        assert fetched is not None

    async def test_create_with_metadata(self, registry: WorkflowRegistry) -> None:
        wf = WorkflowDefinition(id="w2", name="Workflow Two")
        await registry.create(wf, metadata={"owner": "team-workflow", "tags": ["production", "etl"]})
        meta = await registry.get_metadata("w2")
        assert meta["owner"] == "team-workflow"
        assert "production" in meta["tags"]

    async def test_update(self, registry: WorkflowRegistry) -> None:
        await registry.create(WorkflowDefinition(id="w3", name="Old Name"))
        updated = await registry.update("w3", name="New Name", version="2.0.0")
        assert updated.name == "New Name"
        assert updated.version == "2.0.0"

    async def test_update_nonexistent_raises(self, registry: WorkflowRegistry) -> None:
        with pytest.raises(WorkflowNotFoundError):
            await registry.update("nonexistent", name="Nope")

    async def test_delete(self, registry: WorkflowRegistry) -> None:
        await registry.create(WorkflowDefinition(id="w4", name="To Delete"))
        await registry.delete("w4")
        assert await registry.get("w4") is None

    async def test_delete_nonexistent_raises(self, registry: WorkflowRegistry) -> None:
        with pytest.raises(WorkflowNotFoundError):
            await registry.delete("nonexistent")

    async def test_list(self, registry: WorkflowRegistry) -> None:
        await registry.create(WorkflowDefinition(id="l1", name="List1"))
        await registry.create(WorkflowDefinition(id="l2", name="List2"))
        defs = await registry.list_definitions()
        assert len(defs) == 2

    async def test_list_by_tag(self, registry: WorkflowRegistry) -> None:
        await registry.create(
            WorkflowDefinition(id="t1", name="Tagged1"),
            metadata={"tags": ["ml"]},
        )
        await registry.create(
            WorkflowDefinition(id="t2", name="Tagged2"),
            metadata={"tags": ["ml", "production"]},
        )
        ml = await registry.list_definitions(tag="ml")
        prod = await registry.list_definitions(tag="production")
        assert len(ml) == 2
        assert len(prod) == 1

    async def test_duplicate(self, registry: WorkflowRegistry) -> None:
        await registry.create(WorkflowDefinition(id="src1", name="Source"))
        copy = await registry.duplicate("src1", "copy1")
        assert copy.name == "Source (Copy)"
        assert copy.id == "copy1"


class TestWorkflowLifecycle:
    """Workflow lifecycle state transitions."""

    async def test_initial_status(self, registry: WorkflowRegistry) -> None:
        wf = WorkflowDefinition(id="life1", name="Lifecycle1")
        await registry.create(wf)
        status = await registry.get_status("life1")
        assert status == WorkflowStatus.PENDING

    async def test_archive(self, registry: WorkflowRegistry) -> None:
        wf = WorkflowDefinition(id="life2", name="Lifecycle2")
        await registry.create(wf)
        await registry.archive("life2")
        assert await registry.get_status("life2") == WorkflowStatus.ARCHIVED

    async def test_archive_nonexistent_raises(self, registry: WorkflowRegistry) -> None:
        with pytest.raises(WorkflowNotFoundError):
            await registry.archive("nonexistent")


class TestWorkflowEvents:
    """Verify lifecycle events are published."""

    async def test_create_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(WorkflowCreated, collect)
        reg = WorkflowRegistry(event_bus=bus)
        await reg.create(WorkflowDefinition(id="evt1", name="Event1"))
        assert "WorkflowCreated" in events

    async def test_update_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(WorkflowUpdated, collect)
        reg = WorkflowRegistry(event_bus=bus)
        await reg.create(WorkflowDefinition(id="evt2", name="Event2"))
        await reg.update("evt2", name="Updated")
        assert "WorkflowUpdated" in events

    async def test_archive_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(WorkflowArchived, collect)
        reg = WorkflowRegistry(event_bus=bus)
        await reg.create(WorkflowDefinition(id="evt3", name="Event3"))
        await reg.archive("evt3")
        assert "WorkflowArchived" in events

    async def test_multiple_workflows_isolated(self) -> None:
        """Verify different workflow IDs don't interfere."""
        reg = WorkflowRegistry()
        await reg.create(WorkflowDefinition(id="iso1", name="Isolated1"))
        await reg.create(WorkflowDefinition(id="iso2", name="Isolated2"))
        await reg.archive("iso1")
        assert await reg.get_status("iso1") == WorkflowStatus.ARCHIVED
        assert await reg.get_status("iso2") == WorkflowStatus.PENDING
