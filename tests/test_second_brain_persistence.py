"""Focused persistence tests for Second Brain.

These verify that governed Brain state survives a service/process restart by
reloading from the shared PostgreSQL store through a *fresh* service instance
that does not share any in-memory cache with the one that created the data.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.auth.auth_providers import AuthenticationService
from eaip.brain.persistence import SqlSecondBrainRepository
from eaip.brain.second_brain import SecondBrainService
from eaip.http.api import create_app
from eaip.http.routers.brains import _ensure_repository


@pytest.fixture
async def client():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()
    lifecycle.platform.container.register_instance(
        AuthenticationService,
        AuthenticationService(secret="test-secret-do-not-use-in-production"),
    )
    app = create_app(lifecycle)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        login = await c.post("/api/auth/login", json={"email": "persist-owner", "password": "password"})
        c.headers = {"Authorization": f"Bearer {login.json()['token']}"}
        yield c
    await lifecycle.stop()


async def fresh_service() -> SecondBrainService:
    """Build a brand-new service instance backed by the shared DB store.

    This intentionally does NOT reuse the container-cached service so we prove
    the data lives in durable storage rather than process memory.
    """
    repository = await _ensure_repository()
    assert repository is not None, "Database repository must be available for persistence tests"
    return SecondBrainService(repository=repository)


def _owner_id_of(brain: dict[str, object]) -> str:
    return str(brain["ownerId"])


async def test_create_persists(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Persist Create Brain"})
    assert created.status_code == 200
    brain = created.json()
    reloaded = await (await fresh_service()).get(brain["id"], _owner_id_of(brain))
    assert reloaded is not None
    assert reloaded.brain_id == brain["id"]
    assert reloaded.name == "Persist Create Brain"


async def test_read_persists(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "marketing", "name": "Read Brain"})
    brain_id = created.json()["id"]
    owner = _owner_id_of(created.json())
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert reloaded is not None
    assert reloaded.business_function == "Marketing"
    assert reloaded.status == "active"


async def test_update_persists(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Update Brain"})
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)
    configured = await client.put(
        f"/api/brains/{brain_id}/config",
        json={"objectives": ["Grow enterprise revenue"], "instructions": "Be evidence-led."},
    )
    assert configured.status_code == 200
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert reloaded.objectives == ["Grow enterprise revenue"]
    assert reloaded.instructions == "Be evidence-led."


async def test_delete_persists(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Delete Brain"})
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)
    deleted = await client.delete(f"/api/brains/{brain_id}")
    assert deleted.status_code == 200
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert reloaded is None


async def test_config_persistence(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Config Brain"})
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)
    await client.put(
        f"/api/brains/{brain_id}/config",
        json={
            "name": "Configured Brain",
            "description": "Updated description",
            "businessFunction": "Finance",
            "rules": ["Rule one", "Rule two"],
            "tools": ["knowledge.search", "memory.write"],
            "approvalRequired": False,
        },
    )
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert reloaded.name == "Configured Brain"
    assert reloaded.description == "Updated description"
    assert reloaded.business_function == "Finance"
    assert reloaded.rules == ["Rule one", "Rule two"]
    assert reloaded.tools == ["knowledge.search", "memory.write"]
    assert reloaded.approval_required is False


async def test_memory_persistence(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Memory Brain"})
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)
    memory = await client.post(f"/api/brains/{brain_id}/memory", json={"content": "Durable memory note."})
    assert memory.status_code == 200
    memory_id = memory.json()["id"]
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert memory_id in reloaded.memory_ids


async def test_knowledge_relationship_persistence(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Knowledge Brain"})
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)
    await client.put(
        f"/api/brains/{brain_id}/config",
        json={"knowledgeSources": ["marketing-research", "sales-playbook"]},
    )
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert reloaded.knowledge_sources == ["marketing-research", "sales-playbook"]


async def test_mission_relationship_persistence(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Mission Brain"})
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)
    queried = await client.post(f"/api/brains/{brain_id}/query", json={"query": "What next?"})
    rec_id = queried.json()["recommendation"]["id"]
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    mission = await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/mission")
    assert mission.status_code == 200
    mission_id = mission.json()["id"]
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert mission_id in reloaded.mission_ids
    assert any(r.get("missionId") == mission_id for r in reloaded.recommendations)


async def test_activity_relationship_persistence(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Activity Brain"})
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)
    await client.put(f"/api/brains/{brain_id}/config", json={"objectives": ["Track activity"]})
    queried = await client.post(f"/api/brains/{brain_id}/query", json={"query": "Activity?"})
    rec_id = queried.json()["recommendation"]["id"]
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/mission")
    await client.post(f"/api/brains/{brain_id}/memory", json={"content": "Activity memory."})
    reloaded = await (await fresh_service()).get(brain_id, owner)
    actions = {entry["action"] for entry in reloaded.activity}
    assert {"created", "configured", "recommendation_generated", "approval_granted", "mission_created", "memory_recorded"} <= actions


async def test_restart_reload_persistence(client: AsyncClient) -> None:
    """Simulate a backend/service restart and reload the Brain from storage."""
    created = await client.post(
        "/api/brains",
        json={
            "template": "marketing",
            "name": "Restart Survivor",
            "objectives": ["Survive restart"],
            "knowledgeSources": ["marketing-research"],
        },
    )
    assert created.status_code == 200
    brain = created.json()
    brain_id = brain["id"]
    owner = _owner_id_of(brain)

    await client.put(
        f"/api/brains/{brain_id}/config",
        json={"instructions": "Persist across restarts.", "rules": ["Stay durable"]},
    )
    queried = await client.post(f"/api/brains/{brain_id}/query", json={"query": "Restart check?"})
    rec_id = queried.json()["recommendation"]["id"]
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    mission = await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/mission")
    mission_id = mission.json()["id"]
    memory = await client.post(f"/api/brains/{brain_id}/memory", json={"content": "Restart memory."})
    memory_id = memory.json()["id"]

    # Simulate restart: a completely fresh service instance reading from storage.
    reloaded = await (await fresh_service()).get(brain_id, owner)
    assert reloaded is not None
    assert reloaded.name == "Restart Survivor"
    assert reloaded.objectives == ["Survive restart"]
    assert reloaded.knowledge_sources == ["marketing-research"]
    assert reloaded.instructions == "Persist across restarts."
    assert reloaded.rules == ["Stay durable"]
    assert memory_id in reloaded.memory_ids
    assert mission_id in reloaded.mission_ids
    assert any(r.get("missionId") == mission_id for r in reloaded.recommendations)
    expected_actions = {
        "created",
        "configured",
        "recommendation_generated",
        "approval_granted",
        "mission_created",
        "memory_recorded",
    }
    assert expected_actions <= {entry["action"] for entry in reloaded.activity}


async def test_authorization_persists(client: AsyncClient) -> None:
    created = await client.post("/api/brains", json={"template": "custom", "name": "Auth Brain"})
    brain = created.json()
    brain_id = brain["id"]

    other = await client.post(
        "/api/auth/login", json={"email": "other-persist", "password": "password"}
    )
    client.headers = {"Authorization": f"Bearer {other.json()['token']}"}
    denied = await client.get(f"/api/brains/{brain_id}")
    assert denied.status_code == 404

    # Reloading as the other owner through a fresh service must also be denied.
    reloaded = await (await fresh_service()).get(brain_id, "other-persist")
    assert reloaded is None
