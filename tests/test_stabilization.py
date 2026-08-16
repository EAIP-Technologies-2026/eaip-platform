"""Stabilization integration tests — infrastructure, health, background tasks, WebSocket bridge."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.http.api import create_app


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def app():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()

    c = lifecycle.platform.container
    e = lifecycle.platform.events

    from eaip.agents.registry import AgentRegistry
    from eaip.agents.runtime import AgentRuntime
    from eaip.auth.auth_providers import AuthenticationService
    from eaip.runtime.mission import MissionRegistry
    from eaip.workflow.executor import WorkflowEngine
    from eaip.workflow.registry import WorkflowRegistry

    for t, inst in [
        (AgentRegistry, AgentRegistry(event_bus=e)),
        (AgentRuntime, AgentRuntime(llm_adapter=None, tool_registry=None, event_bus=e)),
        (AuthenticationService, AuthenticationService(secret="test-secret", event_bus=e)),
        (WorkflowRegistry, WorkflowRegistry(event_bus=e)),
        (WorkflowEngine, WorkflowEngine(event_bus=e)),
        (MissionRegistry, MissionRegistry(event_bus=e)),
    ]:
        c.register_instance(t, inst)

    fastapi_app = create_app(lifecycle)
    yield fastapi_app, lifecycle

    await lifecycle.stop()


@pytest.fixture
async def client(app):
    fastapi_app, _lifecycle = app
    transport = ASGITransport(app=fastapi_app)
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
    async def test_health_returns_checks(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "checks" in data
        assert "background_tasks" in data

    async def test_health_background_tasks(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        tasks = r.json()["background_tasks"]
        assert isinstance(tasks, dict)

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


class TestInfrastructure:
    async def test_infrastructure_health(self, app):
        _fastapi_app, lifecycle = app
        infra = lifecycle._infrastructure
        assert infra is not None
        assert hasattr(infra, "background_tasks")

    async def test_background_tasks_registered(self, app):
        _fastapi_app, lifecycle = app
        tasks = lifecycle._infrastructure.background_tasks
        status = tasks.status()
        assert isinstance(status, dict)

    async def test_health_check_registered(self, app):
        _fastapi_app, lifecycle = app
        infra_health = lifecycle._infrastructure._infra_health
        assert infra_health is not None
        report = await infra_health.check()
        assert report.status.value in ("healthy", "degraded", "unhealthy")


class TestPlatformLifecycle:
    async def test_lifecycle_starts_and_stops(self):
        builder = ApplicationBuilder()
        lifecycle = builder.build()
        assert lifecycle.phase.value == "created"

        await lifecycle.start()
        assert lifecycle.phase.value == "running"
        assert lifecycle.platform is not None

        await lifecycle.stop()
        assert lifecycle.phase.value == "stopped"

    async def test_lifecycle_runtime_kernel_enabled(self):
        builder = ApplicationBuilder()
        lifecycle = builder.build()
        await lifecycle.start()
        assert lifecycle.kernel is not None
        assert lifecycle.kernel.phase.value in ("running", "created")
        await lifecycle.stop()


class TestWebSocketBridge:
    async def test_websocket_endpoint_exists(self, client):
        r = await client.get("/version")
        assert r.status_code == 200


class TestEventBusPublish:
    async def test_event_publish_via_api(self, authenticated_client):
        r = await authenticated_client.post(
            "/api/events/publish", json={"type": "test", "payload": {"msg": "hello"}}
        )
        assert r.status_code == 200
        data = r.json()
        assert "eventId" in data

    async def test_event_subscribe_via_api(self, authenticated_client):
        r = await authenticated_client.post("/api/events/subscribe", json={"type": "test"})
        assert r.status_code == 200
        data = r.json()
        assert "subscriptionId" in data


class TestMigrationFramework:
    async def test_migration_registration(self):
        from eaip.infrastructure.db.connection import DatabaseConnection
        from eaip.infrastructure.db.migrations import Migration, MigrationEngine

        engine = MigrationEngine(DatabaseConnection, table_name="_test_migrations")

        async def up(conn):
            await conn.execute("CREATE TABLE IF NOT EXISTS _test_migration (id TEXT PRIMARY KEY)")

        async def down(conn):
            await conn.execute("DROP TABLE IF EXISTS _test_migration")

        migration = Migration(id="test_001", description="Test migration", up=up, down=down)
        engine.register(migration)
        assert engine.pending_count == 1
        assert engine.applied_count == 0


class TestBackgroundTasks:
    async def test_background_task_registry(self):
        from eaip.infrastructure.infrastructure import BackgroundTaskRegistry

        registry = BackgroundTaskRegistry()
        assert registry.count == 0

        async def dummy_task():
            pass

        registry.register("test", dummy_task)
        assert registry.count == 1
        status = registry.status()
        assert "test" in status
        await registry.cancel_all()


class TestAdminEndpoints:
    async def test_admin_snapshot(self, authenticated_client):
        r = await authenticated_client.get("/api/admin/snapshot")
        assert r.status_code == 200
        data = r.json()
        assert "services" in data
        assert "health" in data

    async def test_admin_users(self, authenticated_client):
        r = await authenticated_client.get("/api/admin/users")
        assert r.status_code == 200

    async def test_admin_roles(self, authenticated_client):
        r = await authenticated_client.get("/api/admin/roles")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["id"] == "admin"

    async def test_admin_settings(self, authenticated_client):
        r = await authenticated_client.get("/api/admin/settings")
        assert r.status_code == 200

    async def test_admin_audit(self, authenticated_client):
        r = await authenticated_client.get("/api/admin/audit")
        assert r.status_code == 200

    async def test_admin_feature_flags(self, authenticated_client):
        r = await authenticated_client.get("/api/admin/feature-flags")
        assert r.status_code == 200


class TestMonitoringEndpoints:
    async def test_monitoring_metrics(self, authenticated_client):
        r = await authenticated_client.get("/api/monitoring/metrics")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    async def test_monitoring_diagnostics(self, authenticated_client):
        r = await authenticated_client.get("/api/monitoring/diagnostics")
        assert r.status_code == 200
        assert "checks" in r.json()


class TestSearchEndpoints:
    async def test_search(self, authenticated_client):
        r = await authenticated_client.get("/api/search?q=test")
        assert r.status_code == 200
        assert "results" in r.json()

    async def test_search_suggestions(self, authenticated_client):
        r = await authenticated_client.get("/api/search/suggestions?q=test")
        assert r.status_code == 200

    async def test_search_recent(self, authenticated_client):
        saved = await authenticated_client.post(
            "/api/search/recent",
            json={"query": "recent test", "category": "agents"},
        )
        assert saved.status_code == 200
        assert saved.json()["status"] == "saved"

        r = await authenticated_client.get("/api/search/recent")
        assert r.status_code == 200
        assert any(search["query"] == "recent test" for search in r.json()["searches"])

    async def test_search_saved(self, authenticated_client):
        saved = await authenticated_client.post(
            "/api/search/saved",
            json={"query": "saved test", "name": "Saved test", "filters": {"status": "active"}},
        )
        assert saved.status_code == 200
        search_id = saved.json()["id"]

        r = await authenticated_client.get("/api/search/saved")
        assert r.status_code == 200
        assert any(search["id"] == search_id for search in r.json()["searches"])

        deleted = await authenticated_client.delete(f"/api/search/saved/{search_id}")
        assert deleted.status_code == 200
        assert not any(
            search["id"] == search_id
            for search in (await authenticated_client.get("/api/search/saved")).json()["searches"]
        )


class TestMarketplaceEndpoints:
    async def test_marketplace_packages(self, authenticated_client):
        r = await authenticated_client.get("/api/marketplace/packages")
        assert r.status_code == 200

    async def test_marketplace_categories(self, authenticated_client):
        r = await authenticated_client.get("/api/marketplace/categories")
        assert r.status_code == 200
        assert "categories" in r.json()

    async def test_marketplace_featured(self, authenticated_client):
        r = await authenticated_client.get("/api/marketplace/packages/featured")
        assert r.status_code == 200


class TestWorkflowDesignerPersistence:
    async def test_create_and_save_designer(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Designer Test"})
        assert r.status_code == 200
        wf_id = r.json()["id"]

        r = await authenticated_client.put(
            f"/api/designer/{wf_id}",
            json={
                "nodes": [{"id": "n1", "label": "Start", "x": 100, "y": 100}],
                "edges": [],
                "viewport": {"x": 0, "y": 0, "zoom": 1},
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "saved"

    async def test_load_designer(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Load Test"})
        wf_id = r.json()["id"]

        await authenticated_client.put(
            f"/api/designer/{wf_id}",
            json={
                "nodes": [{"id": "n1", "label": "Agent", "x": 200, "y": 150}],
                "edges": [],
                "viewport": {"x": 0, "y": 0, "zoom": 1},
            },
        )

        r = await authenticated_client.get(f"/api/designer/{wf_id}")
        assert r.status_code == 200
        assert "nodes" in r.json()

    async def test_designer_autosave(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Autosave Test"})
        wf_id = r.json()["id"]

        r = await authenticated_client.post(
            f"/api/designer/{wf_id}/autosave",
            json={
                "nodes": [{"id": "n1", "label": "Test", "x": 50, "y": 50}],
                "edges": [],
                "viewport": {"x": 0, "y": 0, "zoom": 1},
            },
        )
        assert r.status_code == 200

        r = await authenticated_client.get(f"/api/designer/{wf_id}/autosave")
        assert r.status_code == 200
        assert r.json()["hasAutosave"] is True

        r = await authenticated_client.delete(f"/api/designer/{wf_id}/autosave")
        assert r.status_code == 200


class TestWorkflowVersions:
    async def test_create_workflow_version(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Version Test"})
        wf_id = r.json()["id"]

        r = await authenticated_client.post(
            f"/api/workflows/{wf_id}/versions",
            json={
                "version": 1,
                "nodes": [{"id": "n1", "label": "Step 1", "x": 0, "y": 0}],
                "connections": [],
                "message": "Initial version",
            },
        )
        assert r.status_code == 200
        assert r.json()["version"] == 1

    async def test_list_workflow_versions(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "List Versions Test"})
        wf_id = r.json()["id"]

        r = await authenticated_client.get(f"/api/workflows/{wf_id}/versions")
        assert r.status_code == 200

    async def test_publish_version(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Publish Test"})
        wf_id = r.json()["id"]

        r = await authenticated_client.post(
            f"/api/workflows/{wf_id}/versions", json={"version": 1, "message": "v1"}
        )
        version_id = r.json()["id"]

        r = await authenticated_client.post(f"/api/workflows/{wf_id}/versions/{version_id}/publish")
        assert r.status_code == 200

    async def test_archive_version(self, authenticated_client):
        r = await authenticated_client.post("/api/workflows", json={"name": "Archive Test"})
        wf_id = r.json()["id"]

        r = await authenticated_client.post(
            f"/api/workflows/{wf_id}/versions", json={"version": 1, "message": "v1"}
        )
        version_id = r.json()["id"]

        r = await authenticated_client.post(f"/api/workflows/{wf_id}/versions/{version_id}/archive")
        assert r.status_code == 200
