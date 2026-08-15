from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.auth.auth_providers import AuthenticationService
from eaip.http.api import create_app


@pytest.fixture
async def authenticated_client():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()
    lifecycle.platform.container.register_instance(
        AuthenticationService,
        AuthenticationService(secret="test-secret-do-not-use-in-production"),
    )
    app = create_app(lifecycle)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login", json={"email": "brain-owner", "password": "password"}
        )
        client.headers = {"Authorization": f"Bearer {login.json()['token']}"}
        yield client
    await lifecycle.stop()


@pytest.mark.asyncio
async def test_marketing_brain_lifecycle(authenticated_client: AsyncClient) -> None:
    templates = await authenticated_client.get("/api/brains/templates")
    assert templates.status_code == 200
    marketing = next(item for item in templates.json() if item["id"] == "marketing")

    created = await authenticated_client.post(
        "/api/brains",
        json={"template": "marketing", "name": marketing["name"]},
    )
    assert created.status_code == 200
    brain = created.json()
    brain_id = brain["id"]
    assert brain["businessFunction"] == "Marketing"
    assert brain["status"] == "active"

    configured = await authenticated_client.put(
        f"/api/brains/{brain_id}/config",
        json={
            "objectives": ["Improve qualified customer acquisition."],
            "knowledgeSources": ["marketing-research"],
            "approvalRequired": True,
        },
    )
    assert configured.status_code == 200
    assert configured.json()["knowledgeSources"] == ["marketing-research"]

    queried = await authenticated_client.post(
        f"/api/brains/{brain_id}/query",
        json={"query": "What should marketing focus on this week?"},
    )
    assert queried.status_code == 200
    recommendation = queried.json()["recommendation"]
    assert recommendation["status"] == "pending_approval"
    recommendation_id = recommendation["id"]

    blocked = await authenticated_client.post(
        f"/api/brains/{brain_id}/recommendations/{recommendation_id}/mission"
    )
    assert blocked.status_code == 403

    approved = await authenticated_client.post(
        f"/api/brains/{brain_id}/recommendations/{recommendation_id}/approve"
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    mission = await authenticated_client.post(
        f"/api/brains/{brain_id}/recommendations/{recommendation_id}/mission"
    )
    assert mission.status_code == 200
    assert mission.json()["id"] in brain["missionIds"] or mission.json()["id"]

    memory = await authenticated_client.post(
        f"/api/brains/{brain_id}/memory",
        json={"content": "Approved focus: qualified customer acquisition."},
    )
    assert memory.status_code == 200
    assert memory.json()["why"]

    activity = await authenticated_client.get(f"/api/brains/{brain_id}/activity")
    assert activity.status_code == 200
    actions = [entry["action"] for entry in activity.json()]
    assert {"created", "configured", "recommendation_generated", "approval_granted", "mission_created", "memory_recorded"} <= set(actions)

    retrieved = await authenticated_client.get(f"/api/brains/{brain_id}")
    assert retrieved.status_code == 200
    assert retrieved.json()["recommendations"][0]["missionId"]


@pytest.mark.asyncio
async def test_brain_owner_isolation(authenticated_client: AsyncClient) -> None:
    created = await authenticated_client.post(
        "/api/brains", json={"template": "marketing", "name": "Private Marketing Brain"}
    )
    brain_id = created.json()["id"]

    other_login = await authenticated_client.post(
        "/api/auth/login", json={"email": "another-owner", "password": "password"}
    )
    authenticated_client.headers = {"Authorization": f"Bearer {other_login.json()['token']}"}
    response = await authenticated_client.get(f"/api/brains/{brain_id}")
    assert response.status_code == 404
