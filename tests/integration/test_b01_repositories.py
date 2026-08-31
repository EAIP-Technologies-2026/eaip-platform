"""B01 — typed tenant-scoped repositories verification."""

from __future__ import annotations

import pytest

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence import (
    AgentRunRepository,
    AuditEventRepository,
    WorkflowRunRepository,
)


@pytest.fixture
async def parents(db: None) -> None:
    await DatabaseConnection.execute("INSERT INTO agents (id, name) VALUES ($1, $2)", "agent-1", "Alpha")
    await DatabaseConnection.execute("INSERT INTO workflows (id, name) VALUES ($1, $2)", "wf-1", "Ingest")


class TestAgentRunRepository:
    async def test_create_get_update(self, db: None, parents: None) -> None:
        repo = AgentRunRepository()
        await repo.create(
            "run-1", agent_id="agent-1", tenant_id="acme", status="running",
            goal_text="index docs", goal_metadata={"priority": 1},
        )
        run = await repo.get("run-1")
        assert run is not None
        assert run["agent_id"] == "agent-1"
        assert run["tenant_id"] == "acme"
        assert run["goal_metadata"]["priority"] == 1

        await repo.update_status("run-1", "completed", result="ok", duration_ms=12.5)
        assert (await repo.get("run-1"))["status"] == "completed"
        assert (await repo.get("run-1"))["duration_ms"] == 12.5

    async def test_tenant_isolation(self, db: None, parents: None) -> None:
        repo = AgentRunRepository()
        await repo.create("run-a", agent_id="agent-1", tenant_id="acme")
        await repo.create("run-b", agent_id="agent-1", tenant_id="globex")
        assert await repo.get_for_tenant("run-a", "globex") is None
        assert await repo.get_for_tenant("run-a", "acme") is not None
        assert len(await repo.list_by_tenant("acme")) == 1
        assert await repo.count(tenant_id="acme") == 1
        assert await repo.count() == 2

    async def test_create_is_idempotent(self, db: None, parents: None) -> None:
        repo = AgentRunRepository()
        await repo.create("run-1", agent_id="agent-1", tenant_id="acme")
        await repo.create("run-1", agent_id="agent-1", tenant_id="acme", status="running")
        assert await repo.count() == 1

    async def test_restart_durability(self, db: None, parents: None, fresh_pool) -> None:
        repo = AgentRunRepository()
        await repo.create("run-1", agent_id="agent-1", tenant_id="acme", status="completed")
        await fresh_pool()
        run = await repo.get("run-1")
        assert run is not None
        assert run["status"] == "completed"


class TestWorkflowRunRepository:
    async def test_create_get_update(self, db: None, parents: None) -> None:
        repo = WorkflowRunRepository()
        await repo.create(
            "wrun-1", workflow_id="wf-1", tenant_id="acme", status="running",
            state="on_node_2", context={"node": 2},
        )
        run = await repo.get("wrun-1")
        assert run is not None
        assert run["workflow_id"] == "wf-1"
        assert run["context"]["node"] == 2

        await repo.update_state("wrun-1", "completed", status="completed", context={"node": 3})
        updated = await repo.get("wrun-1")
        assert updated["state_machine_state"] == "completed"
        assert updated["status"] == "completed"
        assert updated["context"]["node"] == 3

    async def test_tenant_isolation(self, db: None, parents: None) -> None:
        repo = WorkflowRunRepository()
        await repo.create("wrun-a", workflow_id="wf-1", tenant_id="acme")
        await repo.create("wrun-b", workflow_id="wf-1", tenant_id="globex")
        assert await repo.get_for_tenant("wrun-a", "globex") is None
        assert len(await repo.list_by_tenant("globex")) == 1
        assert await repo.count(tenant_id="globex") == 1

    async def test_restart_durability(self, db: None, parents: None, fresh_pool) -> None:
        repo = WorkflowRunRepository()
        await repo.create("wrun-1", workflow_id="wf-1", tenant_id="acme", state="running")
        await fresh_pool()
        run = await repo.get("wrun-1")
        assert run is not None
        assert run["state_machine_state"] == "running"


class TestAuditEventRepository:
    async def test_append_and_query(self, db: None) -> None:
        repo = AuditEventRepository()
        entry_id = await repo.append(
            event_type="auth.login",
            action="login",
            actor_id="user-1",
            resource_type="session",
            resource_id="sess-1",
            changes={"ip": "10.0.0.1"},
            tenant_id="acme",
        )
        assert entry_id
        results = await repo.query("acme", event_type="auth.login")
        assert len(results) == 1
        assert results[0]["id"] == entry_id
        assert results[0]["changes"]["ip"] == "10.0.0.1"

    async def test_query_filters(self, db: None) -> None:
        repo = AuditEventRepository()
        await repo.append(event_type="auth.login", action="login", actor_id="user-1", tenant_id="acme")
        await repo.append(event_type="auth.logout", action="logout", actor_id="user-1", tenant_id="acme")
        await repo.append(event_type="auth.login", action="login", actor_id="user-1", tenant_id="globex")
        assert len(await repo.query("acme", event_type="auth.login")) == 1
        assert len(await repo.query("acme", action="logout")) == 1
        assert len(await repo.query()) == 3

    async def test_append_only_no_mutation_methods(self, db: None) -> None:
        repo = AuditEventRepository()
        assert not hasattr(repo, "update")
        assert not hasattr(repo, "delete")

    async def test_restart_durability(self, db: None, fresh_pool) -> None:
        repo = AuditEventRepository()
        await repo.append(event_type="auth.login", action="login", actor_id="u1", tenant_id="acme")
        await fresh_pool()
        assert await repo.count(tenant_id="acme") == 1