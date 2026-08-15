"""Integration tests for the HTTP API layer.

Tests all REST endpoints against a fully-wired ApplicationLifecycle.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.http.api import create_app


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def app():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()

    c = lifecycle.platform.container
    e = lifecycle.platform.events

    from eaip.agents.registry import AgentRegistry
    from eaip.agents.runtime import AgentRuntime
    from eaip.auth.auth_providers import AuthenticationService
    from eaip.memory.engine import MemoryEngine
    from eaip.memory.store import InMemoryStore
    from eaip.runtime.mission import MissionRegistry
    from eaip.workflow.executor import WorkflowEngine
    from eaip.workflow.registry import WorkflowRegistry
    from eaip.ws.channel_manager import ChannelManager
    from eaip.ws.connection_manager import ConnectionManager
    from eaip.ws.push_service import PushService

    for t, inst in [
        (AgentRegistry, AgentRegistry(event_bus=e)),
        (AgentRuntime, AgentRuntime(llm_adapter=None, tool_registry=None, event_bus=e)),
        (AuthenticationService, AuthenticationService(secret="test-secret", event_bus=e)),
        (MemoryEngine, MemoryEngine(InMemoryStore())),
        (WorkflowRegistry, WorkflowRegistry(event_bus=e)),
        (WorkflowEngine, WorkflowEngine(event_bus=e)),
        (MissionRegistry, MissionRegistry(event_bus=e)),
    ]:
        c.register_instance(t, inst)

    cm = ConnectionManager()
    chm = ChannelManager()
    ps = PushService(channel_manager=chm, connection_manager=cm)
    c.register_instance(ConnectionManager, cm)
    c.register_instance(ChannelManager, chm)
    c.register_instance(PushService, ps)

    fastapi_app = create_app(lifecycle)
    yield fastapi_app

    await lifecycle.stop()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client):
    r = await client.post("/api/auth/login", json={"email": "admin", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


class TestHealth:
    async def test_health_endpoint(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    async def test_ready_endpoint(self, client):
        r = await client.get("/ready")
        assert r.status_code == 200
        assert r.json()["status"] in ("healthy", "degraded", "unhealthy")

    async def test_live_endpoint(self, client):
        r = await client.get("/live")
        assert r.status_code == 200
        assert r.json()["status"] in ("healthy", "degraded", "unhealthy")

    async def test_version_endpoint(self, client):
        r = await client.get("/version")
        assert r.status_code == 200
        assert "version" in r.json()


class TestAuth:
    async def test_login_success(self, client):
        r = await client.post("/api/auth/login", json={"email": "admin", "password": "admin"})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["roles"] == ["admin", "user"]

    async def test_login_invalid_credentials(self, client):
        r = await client.post("/api/auth/login", json={"email": "admin", "password": "invalid"})
        assert r.status_code == 401

    async def test_login_missing_credentials(self, client):
        r = await client.post("/api/auth/login", json={})
        assert r.status_code == 401

    async def test_auth_me(self, authenticated_client):
        r = await authenticated_client.get("/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert "user" in data

    async def test_users_me(self, authenticated_client):
        r = await authenticated_client.get("/api/users/me")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "roles" in data

    async def test_logout(self, authenticated_client):
        r = await authenticated_client.post("/api/auth/logout")
        assert r.status_code == 200

    async def test_update_profile(self, authenticated_client):
        r = await authenticated_client.put("/api/users/me", json={"name": "Updated User"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Updated User"


class TestAgents:
    async def test_list_agents_empty(self, authenticated_client):
        r = await authenticated_client.get("/api/agents")
        assert r.status_code == 200
        assert r.json() == []

    async def test_create_agent(self, authenticated_client):
        r = await authenticated_client.post(
            "/api/agents", json={"name": "Test Agent", "description": "A test"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Agent"
        assert data["status"] == "draft"
        return data["id"]

    async def test_create_and_get_agent(self, authenticated_client):
        r = await authenticated_client.post("/api/agents", json={"name": "Agent 1"})
        agent_id = r.json()["id"]
        r = await authenticated_client.get(f"/api/agents/{agent_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "Agent 1"

    async def test_update_agent(self, authenticated_client):
        r = await authenticated_client.post("/api/agents", json={"name": "Before"})
        agent_id = r.json()["id"]
        r = await authenticated_client.put(f"/api/agents/{agent_id}", json={"name": "After"})
        assert r.status_code == 200
        assert r.json()["name"] == "After"

    async def test_delete_agent(self, authenticated_client):
        r = await authenticated_client.post("/api/agents", json={"name": "To Delete"})
        agent_id = r.json()["id"]
        r = await authenticated_client.delete(f"/api/agents/{agent_id}")
        assert r.status_code == 200
        r = await authenticated_client.get(f"/api/agents/{agent_id}")
        assert r.status_code == 404

    async def test_agent_stats(self, authenticated_client):
        r = await authenticated_client.get("/api/agents/stats")
        assert r.status_code == 200
        data = r.json()
        assert "totalAgents" in data
        assert "runningAgents" in data

    async def test_agent_health(self, authenticated_client):
        r = await authenticated_client.get("/api/agents/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    async def test_agent_duplicate(self, authenticated_client):
        r = await authenticated_client.post("/api/agents", json={"name": "Original"})
        agent_id = r.json()["id"]
        r = await authenticated_client.post(f"/api/agents/{agent_id}/duplicate")
        assert r.status_code == 200
        assert "Copy" in r.json()["name"]

    async def test_agent_archive(self, authenticated_client):
        r = await authenticated_client.post("/api/agents", json={"name": "To Archive"})
        agent_id = r.json()["id"]
        r = await authenticated_client.post(f"/api/agents/{agent_id}/archive")
        assert r.status_code == 200

    async def test_agent_execute(self, authenticated_client):
        r = await authenticated_client.post("/api/agents", json={"name": "Executor"})
        agent_id = r.json()["id"]
        r = await authenticated_client.post(
            f"/api/agents/{agent_id}/execute", json={"input": "hello"}
        )
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "status" in data

    async def test_agent_executions_list(self, authenticated_client):
        r = await authenticated_client.post("/api/agents", json={"name": "Exec Lister"})
        agent_id = r.json()["id"]
        r = await authenticated_client.get(f"/api/agents/{agent_id}/executions")
        assert r.status_code == 200


class TestWorkflows:
    async def test_list_workflows_empty(self, authenticated_client):
        r = await authenticated_client.get("/api/workflows")
        assert r.status_code == 200

    async def test_create_workflow(self, authenticated_client):
        r = await authenticated_client.post(
            "/api/workflows",
            json={
                "name": "Test WF",
                "nodes": [{"id": "s1", "name": "Step 1", "agent_id": "agent-1"}],
                "connections": [],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test WF"

    async def test_get_workflow(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Get Test"})
        wf_id = r.json()["id"]
        r = await authenticated_client.get(f"/api/workflows/{wf_id}")
        assert r.status_code == 200

    async def test_update_workflow(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Before"})
        wf_id = r.json()["id"]
        r = await authenticated_client.put(f"/api/workflows/{wf_id}", json={"name": "After"})
        assert r.status_code == 200
        assert r.json()["name"] == "After"

    async def test_delete_workflow(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Del"})
        wf_id = r.json()["id"]
        r = await authenticated_client.delete(f"/api/workflows/{wf_id}")
        assert r.status_code == 200
        r = await authenticated_client.get(f"/api/workflows/{wf_id}")
        assert r.status_code == 404

    async def test_workflow_stats(self, authenticated_client):
        r = await authenticated_client.get("/api/workflows/stats")
        assert r.status_code == 200
        data = r.json()
        assert "totalWorkflows" in data

    async def test_workflow_health(self, authenticated_client):
        r = await authenticated_client.get("/api/workflows/health")
        assert r.status_code == 200

    async def test_workflow_duplicate(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Orig"})
        wf_id = r.json()["id"]
        r = await authenticated_client.post(f"/api/workflows/{wf_id}/duplicate")
        assert r.status_code == 200

    async def test_workflow_archive(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Arch"})
        wf_id = r.json()["id"]
        r = await authenticated_client.post(f"/api/workflows/{wf_id}/archive")
        assert r.status_code == 200

    async def test_workflow_execute(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Exe"})
        wf_id = r.json()["id"]
        r = await authenticated_client.post(f"/api/workflows/{wf_id}/execute")
        assert r.status_code == 200
        assert "id" in r.json()


class TestMissions:
    async def test_list_missions_empty(self, authenticated_client):
        r = await authenticated_client.get("/api/missions")
        assert r.status_code == 200

    async def test_create_mission(self, authenticated_client):
        r = await authenticated_client.post("/api/missions", json={"name": "Test Mission"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Mission"

    async def test_mission_stats(self, authenticated_client):
        r = await authenticated_client.get("/api/missions/stats")
        assert r.status_code == 200

    async def test_execute_mission(self, authenticated_client):
        r = await authenticated_client.post("/api/missions", json={"name": "Exec"})
        mid = r.json()["id"]
        r = await authenticated_client.post(f"/api/missions/{mid}/execute")
        assert r.status_code == 200


class TestKnowledge:
    async def test_knowledge_stats(self, authenticated_client):
        r = await authenticated_client.get("/api/knowledge/stats")
        assert r.status_code == 200

    async def test_list_collections(self, authenticated_client):
        r = await authenticated_client.get("/api/knowledge/collections")
        assert r.status_code == 200

    async def test_create_collection(self, authenticated_client):
        r = await authenticated_client.post(
            "/api/knowledge/collections", json={"name": "Test Collection"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Collection"

    async def test_list_documents(self, authenticated_client):
        r = await authenticated_client.get("/api/knowledge/documents")
        assert r.status_code == 200

    async def test_search_knowledge(self, authenticated_client):
        r = await authenticated_client.get("/api/knowledge/search?q=test")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "total" in data

    async def test_knowledge_activity(self, authenticated_client):
        r = await authenticated_client.get("/api/knowledge/activity")
        assert r.status_code == 200


class TestRuntime:
    async def test_runtime_metrics(self, authenticated_client):
        r = await authenticated_client.get("/api/runtime/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "runningAgents" in data
        assert "runningWorkflows" in data

    async def test_runtime_health(self, authenticated_client):
        r = await authenticated_client.get("/api/runtime/health")
        assert r.status_code == 200

    async def test_runtime_status(self, authenticated_client):
        r = await authenticated_client.get("/api/runtime/status")
        assert r.status_code == 200


class TestEvents:
    async def test_list_activity(self, authenticated_client):
        r = await authenticated_client.get("/api/events/activity")
        assert r.status_code == 200

    async def test_list_events(self, authenticated_client):
        r = await authenticated_client.get("/api/events")
        assert r.status_code == 200

    async def test_publish_event(self, authenticated_client):
        r = await authenticated_client.post(
            "/api/events/publish", json={"type": "test", "payload": {}}
        )
        assert r.status_code == 200

    async def test_subscribe_event(self, authenticated_client):
        r = await authenticated_client.post("/api/events/subscribe", json={"type": "test"})
        assert r.status_code == 200


class TestMonitoring:
    async def test_monitoring_health(self, authenticated_client):
        r = await authenticated_client.get("/api/monitoring/health")
        assert r.status_code == 200

    async def test_monitoring_metrics(self, authenticated_client):
        r = await authenticated_client.get("/api/monitoring/metrics")
        assert r.status_code == 200

    async def test_monitoring_logs(self, authenticated_client):
        r = await authenticated_client.get("/api/monitoring/logs")
        assert r.status_code == 200


class TestOrganizations:
    async def test_list_orgs(self, authenticated_client):
        r = await authenticated_client.get("/api/organizations")
        assert r.status_code == 200

    async def test_create_org(self, authenticated_client):
        r = await authenticated_client.post("/api/organizations", json={"name": "Test Org"})
        assert r.status_code == 200

    async def test_get_org(self, authenticated_client):
        r = await authenticated_client.get("/api/organizations/org-1")
        assert r.status_code == 200


class TestDeployments:
    async def test_list_deployments(self, authenticated_client):
        r = await authenticated_client.get("/api/deployments")
        assert r.status_code == 200

    async def test_create_deployment(self, authenticated_client):
        r = await authenticated_client.post(
            "/api/deployments", json={"name": "Test", "environment": "prod"}
        )
        assert r.status_code == 200

    async def test_get_deployment(self, authenticated_client):
        r = await authenticated_client.get("/api/deployments/deploy-1")
        assert r.status_code == 200


class TestMemory:
    async def test_memory_graph(self, authenticated_client):
        r = await authenticated_client.get("/api/memory/agents/agent-1/graph")
        assert r.status_code == 200

    async def test_set_and_get_memory(self, authenticated_client):
        r = await authenticated_client.put("/api/memory/my-key", json={"value": "hello"})
        assert r.status_code == 200
        data = r.json()
        assert data["key"] == "my-key"
        assert data["value"] == "hello"
        assert "id" in data
        assert "timestamp" in data

        r = await authenticated_client.get("/api/memory/my-key")
        assert r.status_code == 200
        data = r.json()
        assert data["key"] == "my-key"
        assert data["value"] == "hello"

    async def test_get_memory_not_found(self, authenticated_client):
        r = await authenticated_client.get("/api/memory/nonexistent")
        assert r.status_code == 404

    async def test_delete_memory(self, authenticated_client):
        await authenticated_client.put("/api/memory/to-delete", json={"value": "bye"})
        r = await authenticated_client.delete("/api/memory/to-delete")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "deleted"

        r = await authenticated_client.get("/api/memory/to-delete")
        assert r.status_code == 404

    async def test_list_memory_with_prefix(self, authenticated_client):
        await authenticated_client.put("/api/memory/alpha", json={"value": "a"})
        await authenticated_client.put("/api/memory/beta", json={"value": "b"})
        await authenticated_client.put("/api/memory/gamma", json={"value": "c"})

        r = await authenticated_client.get("/api/memory?prefix=a")
        assert r.status_code == 200
        keys = [e["key"] for e in r.json()]
        assert "alpha" in keys
        assert "beta" not in keys

    async def test_search_memory(self, authenticated_client):
        await authenticated_client.put("/api/memory/searchable", json={"value": "find me"})
        r = await authenticated_client.get("/api/memory/search?q=find")
        assert r.status_code == 200
        keys = [e["key"] for e in r.json()]
        assert "searchable" in keys
