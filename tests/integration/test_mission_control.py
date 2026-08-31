"""Integration tests for Mission Control runtime.

Covers Mission lifecycle, RuntimeRegistry, and event publishing.
"""

from __future__ import annotations

from eaip.events.bus import EventBus
from eaip.runtime.events import (
    MissionCancelled,
    MissionCompleted,
    MissionCreated,
    MissionFailed,
    MissionStarted,
    RuntimeStarted,
    RuntimeStopped,
)
from eaip.runtime.mission import MissionRegistry, MissionStatus
from eaip.runtime.runtime_registry import RuntimeRegistry


class TestMissionLifecycle:
    """Full mission lifecycle from creation to completion."""

    async def test_create_mission(self) -> None:
        registry = MissionRegistry()
        mission = await registry.create(
            mission_id="m1",
            name="Test Mission",
            agent_ids=("agent-1", "agent-2"),
            workflow_ids=("wf-1",),
            knowledge_collections=("docs",),
        )
        assert mission.mission_id == "m1"
        assert mission.name == "Test Mission"
        assert len(mission.agent_ids) == 2
        assert mission.status == MissionStatus.DRAFT

    async def test_full_lifecycle(self) -> None:
        registry = MissionRegistry()
        mission = await registry.create("m2", "Full Lifecycle")
        assert mission.status == MissionStatus.DRAFT

        await mission.queue()
        assert mission.status == MissionStatus.QUEUED

        await mission.start()
        assert mission.status == MissionStatus.RUNNING

        await mission.complete(result="success")
        assert mission.status == MissionStatus.COMPLETED
        assert mission.result == "success"

    async def test_mission_failure(self) -> None:
        registry = MissionRegistry()
        mission = await registry.create("m3", "Failing Mission")
        await mission.start()
        await mission.fail("Something went wrong")
        assert mission.status == MissionStatus.FAILED
        assert mission.error == "Something went wrong"

    async def test_mission_cancellation(self) -> None:
        registry = MissionRegistry()
        mission = await registry.create("m4", "Cancelled Mission")
        await mission.start()
        await mission.cancel()
        assert mission.status == MissionStatus.CANCELLED

    async def test_mission_duration(self) -> None:
        registry = MissionRegistry()
        mission = await registry.create("m5", "Timed Mission")
        await mission.start()
        await mission.complete()
        assert mission.duration_ms > 0

    async def test_get_and_list_missions(self) -> None:
        registry = MissionRegistry()
        await registry.create("m6", "Mission A")
        await registry.create("m7", "Mission B")
        all_m = await registry.list_missions()
        assert len(all_m) == 2

        m = await registry.get("m6")
        assert m is not None
        assert m.mission_id == "m6"


class TestMissionEvents:
    """Verify lifecycle events are published."""

    async def test_mission_events_published(self) -> None:
        bus = EventBus()
        events: list[str] = []

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(MissionCreated, collect)
        bus.subscribe(MissionStarted, collect)
        bus.subscribe(MissionCompleted, collect)
        bus.subscribe(MissionFailed, collect)
        bus.subscribe(MissionCancelled, collect)

        registry = MissionRegistry(event_bus=bus)
        mission = await registry.create("m10", "Eventful Mission")

        assert "MissionCreated" in events
        events.clear()

        await mission.start()
        assert "MissionStarted" in events
        events.clear()

        await mission.complete(result="done")
        assert "MissionCompleted" in events
        events.clear()

        mission2 = await registry.create("m11", "Failing")
        await mission2.start()
        await mission2.fail("error")
        assert "MissionFailed" in events

    async def test_mission_stats(self) -> None:
        registry = MissionRegistry()
        m1 = await registry.create("s1", "Stats1")
        m2 = await registry.create("s2", "Stats2")
        m3 = await registry.create("s3", "Stats3")

        await m1.start()
        await m1.complete()

        await m2.start()
        await m2.fail("error")

        await m3.start()

        stats = registry.get_stats()
        assert stats["total"] == 3
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["running"] == 1


class TestRuntimeRegistry:
    """RuntimeRegistry component tracking."""

    async def test_start_stop(self) -> None:
        reg = RuntimeRegistry()
        assert reg.get_snapshot()["health_status"] == "starting"

        await reg.start()
        assert reg.get_snapshot()["health_status"] == "healthy"

        await reg.stop()
        assert reg.get_snapshot()["health_status"] == "stopped"

    async def test_counts(self) -> None:
        reg = RuntimeRegistry()
        reg.active_agents = 5
        reg.active_workflows = 3
        reg.active_sessions = 10
        snap = reg.get_snapshot()
        assert snap["active_agents"] == 5
        assert snap["active_workflows"] == 3
        assert snap["active_sessions"] == 10

    async def test_runtime_events_published(self) -> None:
        bus = EventBus()
        events: list[str] = []

        async def collect(e: object) -> None:
            events.append(type(e).__name__)

        bus.subscribe(RuntimeStarted, collect)
        bus.subscribe(RuntimeStopped, collect)

        reg = RuntimeRegistry(event_bus=bus)
        await reg.start()
        await reg.stop()

        assert "RuntimeStarted" in events
        assert "RuntimeStopped" in events

    async def test_uptime(self) -> None:
        import time

        reg = RuntimeRegistry()
        u1 = reg.get_snapshot()["uptime_seconds"]
        time.sleep(0.01)
        u2 = reg.get_snapshot()["uptime_seconds"]
        assert u2 > u1

    async def test_mission_to_dict(self) -> None:
        registry = MissionRegistry()
        mission = await registry.create(
            "d1",
            "Dict Mission",
            agent_ids=("a1",),
            workflow_ids=("w1",),
        )
        d = mission.to_dict()
        assert d["mission_id"] == "d1"
        assert d["name"] == "Dict Mission"
        assert d["status"] == "draft"
        assert d["agent_ids"] == ["a1"]
