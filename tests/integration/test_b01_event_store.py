"""B01 — durable PostgreSQL event store verification."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from eaip.events.event import DomainEvent
from eaip.events.store_pg import PgEventStore


class _AgentTaskCompleted(DomainEvent):
    event_type = "test.agent_task_completed"
    agent_id: str
    task: str


class _WorkflowFinished(DomainEvent):
    event_type = "test.workflow_finished"
    workflow_id: str


class _MissionStarted(DomainEvent):
    event_type = "test.mission_started"
    mission_id: str


class TestPgEventStore:
    async def test_record_and_count(self, db: None) -> None:
        store = PgEventStore()
        await store.record(_AgentTaskCompleted(agent_id="a1", task="t1", tenant_id="t-1"))
        await store.record(_WorkflowFinished(workflow_id="w1", tenant_id="t-1"))
        assert await store.count() == 2
        assert await store.count(tenant_id="t-1") == 2
        assert await store.count(tenant_id="t-other") == 0

    async def test_recent_newest_first(self, db: None) -> None:
        store = PgEventStore()
        base = datetime.now(UTC) - timedelta(seconds=10)
        for i in range(3):
            await store.record(
                _AgentTaskCompleted(
                    agent_id="a1",
                    task=f"task-{i}",
                    occurred_at=base + timedelta(seconds=i),
                    tenant_id="t-1",
                )
            )
        recent = await store.recent(limit=2)
        assert len(recent) == 2
        assert recent[0]["action"] == "Agent Task Completed"

    async def test_recent_by_filters(self, db: None) -> None:
        store = PgEventStore()
        await store.record(_AgentTaskCompleted(agent_id="a1", task="x", tenant_id="t-1"))
        await store.record(_AgentTaskCompleted(agent_id="a2", task="y", tenant_id="t-1"))
        await store.record(_WorkflowFinished(workflow_id="w1", tenant_id="t-1"))

        agent_hits = await store.recent_by(agent_id="a1")
        assert len(agent_hits) == 1
        assert agent_hits[0]["id"]

        type_hits = await store.recent_by(type="system")
        assert len(type_hits) == 3

        wf_hits = await store.recent_by(workflow_id="w1")
        assert len(wf_hits) == 1

    async def test_tenant_isolation(self, db: None) -> None:
        store = PgEventStore()
        await store.record(_AgentTaskCompleted(agent_id="a1", task="x", tenant_id="acme"))
        await store.record(_AgentTaskCompleted(agent_id="a2", task="y", tenant_id="globex"))
        acme = await store.recent_by_tenant("acme")
        assert len(acme) == 1
        assert acme[0]["tenant_id"] == "acme"

    async def test_stable_id_deduplicates(self, db: None) -> None:
        store = PgEventStore()
        event = _AgentTaskCompleted(agent_id="a1", task="dedupe", tenant_id="t-1")
        await store.record(event)
        await store.record(event)
        assert await store.count() == 1

    async def test_stored_events_ordered_asc(self, db: None) -> None:
        store = PgEventStore()
        base = datetime.now(UTC) - timedelta(seconds=5)
        for i in range(3):
            await store.record(
                _AgentTaskCompleted(
                    agent_id="a1", task=f"t{i}", occurred_at=base + timedelta(seconds=i)
                )
            )
        events = await store.stored_events(limit=0)
        assert [e["payload"]["task"] for e in events] == ["t0", "t1", "t2"]

    async def test_stored_events_by_type_and_tenant(self, db: None) -> None:
        store = PgEventStore()
        await store.record(_AgentTaskCompleted(agent_id="a1", task="x", tenant_id="acme"))
        await store.record(_WorkflowFinished(workflow_id="w1", tenant_id="acme"))
        agents = await store.stored_events(event_type="_AgentTaskCompleted", tenant_id="acme")
        assert len(agents) == 1

    async def test_restart_durability(self, db: None, fresh_pool) -> None:
        store = PgEventStore()
        event = _AgentTaskCompleted(agent_id="a1", task="durable", tenant_id="acme")
        await store.record(event)
        await fresh_pool()
        assert await store.count() == 1
        assert await store.count(tenant_id="acme") == 1


class TestDomainEventIdentity:
    async def test_defaults(self) -> None:
        event = _AgentTaskCompleted(agent_id="a1", task="x")
        assert event.id
        assert event.tenant_id is None

    async def test_tenant_id_preserved(self) -> None:
        event = _AgentTaskCompleted(agent_id="a1", task="x", tenant_id="acme")
        assert event.tenant_id == "acme"
        assert event.model_dump()["tenant_id"] == "acme"