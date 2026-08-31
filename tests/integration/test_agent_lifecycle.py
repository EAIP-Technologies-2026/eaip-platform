"""Integration tests for agent lifecycle management.

Covers registration, lifecycle transitions, event publishing,
and workspace isolation.
"""

from __future__ import annotations

import pytest

from eaip.agents.events import (
    AgentCreated,
    AgentDeleted,
    AgentFailed,
    AgentPaused,
    AgentStarted,
    AgentStopped,
    AgentUpdated,
)
from eaip.agents.exceptions import AgentNotFoundError
from eaip.agents.models import AgentSpec, AgentStatus
from eaip.agents.registry import AgentRegistry
from eaip.events.bus import EventBus


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def registry(event_bus: EventBus) -> AgentRegistry:
    return AgentRegistry(event_bus=event_bus)


@pytest.fixture
def sample_agent() -> AgentSpec:
    return AgentSpec(
        id="agent-1",
        name="Test Agent",
        description="An agent for integration testing",
        version="1.0.0",
        tools=("web_search", "calculator"),
    )


class TestAgentRegistry:
    """Agent registry CRUD and lifecycle."""

    async def test_create_agent(self, registry: AgentRegistry) -> None:
        agent = AgentSpec(id="a1", name="Agent One")
        created = await registry.create(agent)
        assert created.id == "a1"
        assert created.name == "Agent One"

        fetched = await registry.get("a1")
        assert fetched is not None
        assert fetched.id == "a1"

    async def test_create_with_metadata(self, registry: AgentRegistry) -> None:
        agent = AgentSpec(id="a2", name="Agent Two")
        await registry.create(agent, metadata={"owner": "team-ai", "tags": ["nlp", "production"]})
        meta = await registry.get_metadata("a2")
        assert meta["owner"] == "team-ai"
        assert "nlp" in meta["tags"]

    async def test_create_duplicate(self, registry: AgentRegistry) -> None:
        agent = AgentSpec(id="a3", name="Agent Three")
        await registry.create(agent)
        await registry.create(agent)  # should overwrite
        assert await registry.get("a3") is not None

    async def test_update_agent(self, registry: AgentRegistry) -> None:
        agent = AgentSpec(id="a4", name="Old Name", version="0.1.0")
        await registry.create(agent)
        updated = await registry.update("a4", name="New Name", version="0.2.0")
        assert updated.name == "New Name"
        assert updated.version == "0.2.0"

    async def test_update_nonexistent_raises(self, registry: AgentRegistry) -> None:
        with pytest.raises(AgentNotFoundError):
            await registry.update("nonexistent", name="Nope")

    async def test_delete_agent(self, registry: AgentRegistry) -> None:
        agent = AgentSpec(id="a5", name="To Delete")
        await registry.create(agent)
        await registry.delete("a5")
        assert await registry.get("a5") is None

    async def test_delete_nonexistent_raises(self, registry: AgentRegistry) -> None:
        with pytest.raises(AgentNotFoundError):
            await registry.delete("nonexistent")

    async def test_list_agents(self, registry: AgentRegistry) -> None:
        await registry.create(AgentSpec(id="l1", name="List1"))
        await registry.create(AgentSpec(id="l2", name="List2"))
        agents = await registry.list_agents()
        assert len(agents) == 2

    async def test_list_by_status(self, registry: AgentRegistry) -> None:
        await registry.create(AgentSpec(id="s1", name="Status1"))
        await registry.transition_to("s1", AgentStatus.RUNNING)
        await registry.create(AgentSpec(id="s2", name="Status2"))
        running = await registry.list_agents(status=AgentStatus.RUNNING)
        draft = await registry.list_agents(status=AgentStatus.DRAFT)
        assert len(running) == 1
        assert len(draft) == 1

    async def test_list_by_tag(self, registry: AgentRegistry) -> None:
        await registry.create(
            AgentSpec(id="t1", name="Tag1"),
            metadata={"tags": ["ml", "production"]},
        )
        await registry.create(
            AgentSpec(id="t2", name="Tag2"),
            metadata={"tags": ["ml"]},
        )
        ml_agents = await registry.list_agents(tag="ml")
        production_agents = await registry.list_agents(tag="production")
        assert len(ml_agents) == 2
        assert len(production_agents) == 1


class TestAgentLifecycle:
    """Agent lifecycle state transitions."""

    async def test_initial_status_is_draft(self, registry: AgentRegistry) -> None:
        await registry.create(AgentSpec(id="life1", name="Lifecycle1"))
        status = await registry.get_status("life1")
        assert status == AgentStatus.DRAFT

    async def test_transition_to_running(self, registry: AgentRegistry) -> None:
        await registry.create(AgentSpec(id="life2", name="Lifecycle2"))
        await registry.transition_to("life2", AgentStatus.RUNNING)
        status = await registry.get_status("life2")
        assert status == AgentStatus.RUNNING

    async def test_full_lifecycle(self, registry: AgentRegistry) -> None:
        await registry.create(AgentSpec(id="life3", name="Lifecycle3"))
        assert await registry.get_status("life3") == AgentStatus.DRAFT

        await registry.transition_to("life3", AgentStatus.READY)
        assert await registry.get_status("life3") == AgentStatus.READY

        await registry.transition_to("life3", AgentStatus.RUNNING)
        assert await registry.get_status("life3") == AgentStatus.RUNNING

        await registry.transition_to("life3", AgentStatus.PAUSED)
        assert await registry.get_status("life3") == AgentStatus.PAUSED

        await registry.transition_to("life3", AgentStatus.STOPPED)
        assert await registry.get_status("life3") == AgentStatus.STOPPED

    async def test_transition_nonexistent_raises(self, registry: AgentRegistry) -> None:
        with pytest.raises(AgentNotFoundError):
            await registry.transition_to("nonexistent", AgentStatus.RUNNING)

    async def test_archived_status(self, registry: AgentRegistry) -> None:
        await registry.create(AgentSpec(id="life4", name="Lifecycle4"))
        await registry.transition_to("life4", AgentStatus.ARCHIVED)
        status = await registry.get_status("life4")
        assert status == AgentStatus.ARCHIVED


class TestAgentEvents:
    """Verify lifecycle events are published."""

    async def test_create_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(AgentCreated, collect)
        reg = AgentRegistry(event_bus=bus)
        await reg.create(AgentSpec(id="evt1", name="Event1"))
        assert "AgentCreated" in events

    async def test_update_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(AgentUpdated, collect)
        reg = AgentRegistry(event_bus=bus)
        await reg.create(AgentSpec(id="evt2", name="Event2"))
        await reg.update("evt2", name="Updated")
        assert "AgentUpdated" in events

    async def test_delete_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(AgentDeleted, collect)
        reg = AgentRegistry(event_bus=bus)
        await reg.create(AgentSpec(id="evt3", name="Event3"))
        await reg.delete("evt3")
        assert "AgentDeleted" in events

    async def test_lifecycle_transitions_publish_events(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(AgentStarted, collect)
        bus.subscribe(AgentPaused, collect)
        bus.subscribe(AgentStopped, collect)
        bus.subscribe(AgentFailed, collect)

        reg = AgentRegistry(event_bus=bus)
        await reg.create(AgentSpec(id="evt4", name="Event4"))
        await reg.transition_to("evt4", AgentStatus.RUNNING)
        await reg.transition_to("evt4", AgentStatus.PAUSED)
        await reg.transition_to("evt4", AgentStatus.STOPPED)

        assert "AgentStarted" in events
        assert "AgentPaused" in events
        assert "AgentStopped" in events

    async def test_multiple_agents_isolated(self) -> None:
        """Verify agents with different IDs don't interfere."""
        reg = AgentRegistry()
        await reg.create(AgentSpec(id="iso1", name="Isolated1"))
        await reg.create(AgentSpec(id="iso2", name="Isolated2"))

        await reg.transition_to("iso1", AgentStatus.RUNNING)
        assert await reg.get_status("iso1") == AgentStatus.RUNNING
        assert await reg.get_status("iso2") == AgentStatus.DRAFT
