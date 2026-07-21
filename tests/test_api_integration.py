"""Integration tests for the HTTP API layer.

Tests all REST endpoints against a fully-wired ApplicationLifecycle.
"""

from __future__ import annotations

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

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
    from eaip.workflow.registry import WorkflowRegistry
    from eaip.workflow.executor import WorkflowEngine
    from eaip.runtime.mission import MissionRegistry
    from eaip.ws.channel_manager import ChannelManager
    from eaip.ws.connection_manager import ConnectionManager
    from eaip.ws.push_service import PushService

    for t, inst in [
        (AgentRegistry, AgentRegistry(event_bus=e)),
        (AgentRuntime, AgentRuntime(llm_adapter=None, tool_registry=None, event_bus=e)),
        (AuthenticationService, AuthenticationService(secret="test-secret", event_bus=e)),
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
async def auth_token(client):
    r = await client.post("/auth/login", json={"email": "admin", "password": "admin"})
    assert r.status_code == 200
    return r.json()["token"]


class TestHealth:
    async def test_health_endpoint(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    async def test_ready_endpoint(self, client):
        r = await client.get("/ready")
        assert r.status_code == 200
        assert r.json()["status"] == "ready"

    async def test_live_endpoint(self, client):
        r = await client.get("/live")
        assert r.status_code == 200
        assert r.json()["status"] == "alive"

    async def test_version_endpoint(self, client):
        r = await client.get("/version")
        assert r.status_code == 200
        assert "version" in r.json()


class TestAuth:
    async def test_login_success(self, client):
        r = await client.post("/auth/login", json={"email": "admin", "password": "admin"})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["roles"] == ["admin", "user"]

    async def test_login_invalid_credentials(self, client):
        r = await client.post("/auth/login", json={"email": "admin", "password": "invalid"})
        assert r.status_code == 401

    async def test_login_missing_credentials(self, client):
        r = await client.post("/auth/login", json={})
        assert r.status_code == 401

    async def test_auth_me(self, client, auth_token):
        r = await client.get("/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert "user" in data

    async def test_users_me(self, client, auth_token):
        r = await client.get("/users/me")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "roles" in data

    async def test_logout(self, client, auth_token):
        r = await client.post("/auth/logout")
        assert r.status_code == 200

    async def test_update_profile(self, client, auth_token):
        r = await client.put("/users/me", json={"name": "Updated User"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Updated User"


class TestAgents:
    async def test_list_agents_empty(self, client):
        r = await client.get("/agents")
        assert r.status_code == 200
        assert r.json() == []

    async def test_create_agent(self, client):
        r = await client.post("/agents", json={"name": "Test Agent", "description": "A test"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Agent"
        assert data["status"] == "draft"
        return data["id"]

    async def test_create_and_get_agent(self, client):
        r = await client.post("/agents", json={"name": "Agent 1"})
        agent_id = r.json()["id"]
        r = await client.get(f"/agents/{agent_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "Agent 1"

    async def test_update_agent(self, client):
        r = await client.post("/agents", json={"name": "Before"})
        agent_id = r.json()["id"]
        r = await client.put(f"/agents/{agent_id}", json={"name": "After"})
        assert r.status_code == 200
        assert r.json()["name"] == "After"

    async def test_delete_agent(self, client):
        r = await client.post("/agents", json={"name": "To Delete"})
        agent_id = r.json()["id"]
        r = await client.delete(f"/agents/{agent_id}")
        assert r.status_code == 200
        r = await client.get(f"/agents/{agent_id}")
        assert r.status_code == 404

    async def test_agent_stats(self, client):
        r = await client.get("/agents/stats")
        assert r.status_code == 200
        data = r.json()
        assert "totalAgents" in data
        assert "runningAgents" in data

    async def test_agent_health(self, client):
        r = await client.get("/agents/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    async def test_agent_duplicate(self, client):
        r = await client.post("/agents", json={"name": "Original"})
        agent_id = r.json()["id"]
        r = await client.post(f"/agents/{agent_id}/duplicate")
        assert r.status_code == 200
        assert "Copy" in r.json()["name"]

    async def test_agent_archive(self, client):
        r = await client.post("/agents", json={"name": "To Archive"})
        agent_id = r.json()["id"]
        r = await client.post(f"/agents/{agent_id}/archive")
        assert r.status_code == 200

    async def test_agent_execute(self, client):
        r = await client.post("/agents", json={"name": "Executor"})
        agent_id = r.json()["id"]
        r = await client.post(f"/agents/{agent_id}/execute", json={"input": "hello"})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "status" in data

    async def test_agent_executions_list(self, client):
        r = await client.post("/agents", json={"name": "Exec Lister"})
        agent_id = r.json()["id"]
        r = await client.get(f"/agents/{agent_id}/executions")
        assert r.status_code == 200


class TestWorkflows:
    async def test_list_workflows_empty(self, client):
        r = await client.get("/workflows")
        assert r.status_code == 200

    async def test_create_workflow(self, client):
        r = await client.post("/workflows", json={"name": "Test WF", "nodes": [{"id": "s1", "name": "Step 1", "agent_id": "agent-1"}], "connections": []})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test WF"

    async def test_get_workflow(self, client):
        r = await client.post("/workflows", json={"name": "Get Test"})
        wf_id = r.json()["id"]
        r = await client.get(f"/workflows/{wf_id}")
        assert r.status_code == 200

    async def test_update_workflow(self, client):
        r = await client.post("/workflows", json={"name": "Before"})
        wf_id = r.json()["id"]
        r = await client.put(f"/workflows/{wf_id}", json={"name": "After"})
        assert r.status_code == 200
        assert r.json()["name"] == "After"

    async def test_delete_workflow(self, client):
        r = await client.post("/workflows", json={"name": "Del"})
        wf_id = r.json()["id"]
        r = await client.delete(f"/workflows/{wf_id}")
        assert r.status_code == 200
        r = await client.get(f"/workflows/{wf_id}")
        assert r.status_code == 404

    async def test_workflow_stats(self, client):
        r = await client.get("/workflows/stats")
        assert r.status_code == 200
        data = r.json()
        assert "totalWorkflows" in data

    async def test_workflow_health(self, client):
        r = await client.get("/workflows/health")
        assert r.status_code == 200

    async def test_workflow_duplicate(self, client):
        r = await client.post("/workflows", json={"name": "Orig"})
        wf_id = r.json()["id"]
        r = await client.post(f"/workflows/{wf_id}/duplicate")
        assert r.status_code == 200

    async def test_workflow_archive(self, client):
        r = await client.post("/workflows", json={"name": "Arch"})
        wf_id = r.json()["id"]
        r = await client.post(f"/workflows/{wf_id}/archive")
        assert r.status_code == 200

    async def test_workflow_execute(self, client):
        r = await client.post("/workflows", json={"name": "Exe"})
        wf_id = r.json()["id"]
        r = await client.post(f"/workflows/{wf_id}/execute")
        assert r.status_code == 200
        assert "id" in r.json()


class TestMissions:
    async def test_list_missions_empty(self, client):
        r = await client.get("/missions")
        assert r.status_code == 200

    async def test_create_mission(self, client):
        r = await client.post("/missions", json={"name": "Test Mission"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Mission"

    async def test_mission_stats(self, client):
        r = await client.get("/missions/stats")
        assert r.status_code == 200

    async def test_execute_mission(self, client):
        r = await client.post("/missions", json={"name": "Exec"})
        mid = r.json()["id"]
        r = await client.post(f"/missions/{mid}/execute")
        assert r.status_code == 200


class TestKnowledge:
    async def test_knowledge_stats(self, client):
        r = await client.get("/knowledge/stats")
        assert r.status_code == 200

    async def test_list_collections(self, client):
        r = await client.get("/knowledge/collections")
        assert r.status_code == 200

    async def test_create_collection(self, client):
        r = await client.post("/knowledge/collections", json={"name": "Test Collection"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Collection"

    async def test_list_documents(self, client):
        r = await client.get("/knowledge/documents")
        assert r.status_code == 200

    async def test_search_knowledge(self, client):
        r = await client.get("/knowledge/search?q=test")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "total" in data

    async def test_knowledge_activity(self, client):
        r = await client.get("/knowledge/activity")
        assert r.status_code == 200


class TestRuntime:
    async def test_runtime_metrics(self, client):
        r = await client.get("/runtime/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "runningAgents" in data
        assert "runningWorkflows" in data

    async def test_runtime_health(self, client):
        r = await client.get("/runtime/health")
        assert r.status_code == 200

    async def test_runtime_status(self, client):
        r = await client.get("/runtime/status")
        assert r.status_code == 200


class TestEvents:
    async def test_list_activity(self, client):
        r = await client.get("/events/activity")
        assert r.status_code == 200

    async def test_list_events(self, client):
        r = await client.get("/events")
        assert r.status_code == 200

    async def test_publish_event(self, client):
        r = await client.post("/events/publish", json={"type": "test", "payload": {}})
        assert r.status_code == 200

    async def test_subscribe_event(self, client):
        r = await client.post("/events/subscribe", json={"type": "test"})
        assert r.status_code == 200


class TestMonitoring:
    async def test_monitoring_health(self, client):
        r = await client.get("/monitoring/health")
        assert r.status_code == 200

    async def test_monitoring_metrics(self, client):
        r = await client.get("/monitoring/metrics")
        assert r.status_code == 200

    async def test_monitoring_logs(self, client):
        r = await client.get("/monitoring/logs")
        assert r.status_code == 200


class TestOrganizations:
    async def test_list_orgs(self, client):
        r = await client.get("/organizations")
        assert r.status_code == 200

    async def test_create_org(self, client):
        r = await client.post("/organizations", json={"name": "Test Org"})
        assert r.status_code == 200

    async def test_get_org(self, client):
        r = await client.get("/organizations/org-1")
        assert r.status_code == 200


class TestDeployments:
    async def test_list_deployments(self, client):
        r = await client.get("/deployments")
        assert r.status_code == 200

    async def test_create_deployment(self, client):
        r = await client.post("/deployments", json={"name": "Test", "environment": "prod"})
        assert r.status_code == 200

    async def test_get_deployment(self, client):
        r = await client.get("/deployments/deploy-1")
        assert r.status_code == 200


class TestMemory:
    async def test_memory_graph(self, client):
        r = await client.get("/memory/agents/agent-1/graph")
        assert r.status_code == 200

    async def test_get_memory(self, client):
        r = await client.get("/memory/mem-1")
        assert r.status_code == 200

    async def test_search_memory(self, client):
        r = await client.get("/memory/search?q=test")
        assert r.status_code == 200
