"""Integration tests for the Workspace vertical slice — CRUD, sharing, resource management."""

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
    from eaip.session.workspace import WorkspaceManager

    for t, inst in [
        (AgentRegistry, AgentRegistry(event_bus=e)),
        (AgentRuntime, AgentRuntime(llm_adapter=None, tool_registry=None, event_bus=e)),
        (AuthenticationService, AuthenticationService(secret="test-secret", event_bus=e)),
        (WorkflowRegistry, WorkflowRegistry(event_bus=e)),
        (WorkflowEngine, WorkflowEngine(event_bus=e)),
        (MissionRegistry, MissionRegistry(event_bus=e)),
        (WorkspaceManager, WorkspaceManager(event_bus=e)),
    ]:
        c.register_instance(t, inst)

    fastapi_app = create_app(lifecycle)
    yield fastapi_app
    await lifecycle.stop()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client):
    r = await client.post("/api/auth/login", json={"email": "admin", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


class TestWorkspaceCRUD:
    async def test_list_workspaces_empty(self, auth_client):
        r = await auth_client.get("/api/workspaces")
        assert r.status_code == 200
        assert r.json() == []

    async def test_create_workspace(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "My Workspace"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "My Workspace"
        assert data["ownerId"] is not None
        assert data["status"] == "active"
        assert "id" in data
        return data["id"]

    async def test_create_and_get_workspace(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Test WS"})
        ws_id = r.json()["id"]
        r = await auth_client.get(f"/api/workspaces/{ws_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "Test WS"

    async def test_get_nonexistent_workspace(self, auth_client):
        r = await auth_client.get("/api/workspaces/nonexistent")
        assert r.status_code == 404

    async def test_update_workspace(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Before"})
        ws_id = r.json()["id"]
        r = await auth_client.put(f"/api/workspaces/{ws_id}", json={"name": "After"})
        assert r.status_code == 200
        assert r.json()["name"] == "After"

    async def test_list_workspaces_after_create(self, auth_client):
        r = await auth_client.get("/api/workspaces")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    async def test_archive_workspace(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "To Archive"})
        ws_id = r.json()["id"]
        r = await auth_client.post(f"/api/workspaces/{ws_id}/archive")
        assert r.status_code == 200
        assert r.json()["status"] == "archived"


class TestWorkspaceResources:
    async def test_add_resource(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Resource Test"})
        ws_id = r.json()["id"]
        r = await auth_client.post(f"/api/workspaces/{ws_id}/resources", json={"resourceId": "agent-1"})
        assert r.status_code == 200
        assert r.json()["status"] == "added"
        r = await auth_client.get(f"/api/workspaces/{ws_id}")
        assert "agent-1" in r.json()["resourceIds"]

    async def test_remove_resource(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Remove Test"})
        ws_id = r.json()["id"]
        await auth_client.post(f"/api/workspaces/{ws_id}/resources", json={"resourceId": "wf-1"})
        r = await auth_client.delete(f"/api/workspaces/{ws_id}/resources/wf-1")
        assert r.status_code == 200
        assert r.json()["status"] == "removed"

    async def test_add_resource_missing_id(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Missing"})
        ws_id = r.json()["id"]
        r = await auth_client.post(f"/api/workspaces/{ws_id}/resources", json={})
        assert r.status_code == 422

    async def test_remove_nonexistent_resource(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Nonexistent"})
        ws_id = r.json()["id"]
        r = await auth_client.delete(f"/api/workspaces/{ws_id}/resources/nonexistent")
        assert r.status_code == 404


class TestWorkspaceSharing:
    async def test_share_workspace(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Share Test"})
        ws_id = r.json()["id"]
        r = await auth_client.post(f"/api/workspaces/{ws_id}/share", json={"userId": "user-2"})
        assert r.status_code == 200
        assert r.json()["status"] == "shared"
        r = await auth_client.get(f"/api/workspaces/{ws_id}")
        assert "user-2" in r.json()["sharedWith"]

    async def test_unshare_workspace(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Unshare Test"})
        ws_id = r.json()["id"]
        await auth_client.post(f"/api/workspaces/{ws_id}/share", json={"userId": "user-3"})
        r = await auth_client.post(f"/api/workspaces/{ws_id}/unshare", json={"userId": "user-3"})
        assert r.status_code == 200
        assert r.json()["status"] == "unshared"

    async def test_share_missing_user_id(self, auth_client):
        r = await auth_client.post("/api/workspaces", json={"name": "Missing User"})
        ws_id = r.json()["id"]
        r = await auth_client.post(f"/api/workspaces/{ws_id}/share", json={})
        assert r.status_code == 422

    async def test_list_shared_workspaces(self, auth_client):
        r = await auth_client.get("/api/workspaces/shared")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestWorkspaceAuth:
    async def test_unauthenticated_access(self, client):
        r = await client.get("/api/workspaces")
        assert r.status_code == 401

    async def test_unauthenticated_create(self, client):
        r = await client.post("/api/workspaces", json={"name": "Hack"})
        assert r.status_code == 401
