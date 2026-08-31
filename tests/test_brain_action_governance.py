"""Focused governance regression tests for the Brain Action Center.

These tests verify the security guarantees that must hold for governed AI
execution: approval enforcement, state-machine integrity, idempotency,
and authorization isolation.

They exercise the service directly (unit-level) AND through the HTTP API
(integration-level) to ensure both layers enforce the same invariants.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.auth.auth_providers import AuthenticationService
from eaip.brain.second_brain import SecondBrain, SecondBrainService
from eaip.http.api import create_app
from eaip.runtime.mission import Mission, MissionRegistry


# ── Fixtures ──────────────────────────────────────────────────────────


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
        login = await c.post(
            "/api/auth/login", json={"email": "gov-owner", "password": "password"}
        )
        c.headers = {"Authorization": f"Bearer {login.json()['token']}"}
        yield c
    await lifecycle.stop()


async def _create_brain_with_rec(client: AsyncClient, approval_required: bool = True):
    """Create a brain and generate a recommendation via the API."""
    created = await client.post(
        "/api/brains",
        json={"template": "custom", "name": "Governance Brain", "approvalRequired": approval_required},
    )
    brain_id = created.json()["id"]
    queried = await client.post(
        f"/api/brains/{brain_id}/query", json={"query": "What should we do?"}
    )
    rec_id = queried.json()["recommendation"]["id"]
    return brain_id, rec_id


# ── Unit-level service tests ───────────────────────────────────────────


def _make_brain(approval_required: bool = True) -> SecondBrain:
    brain = SecondBrain(
        brain_id="test-brain",
        name="Test",
        description="Test brain",
        business_function="Test",
        owner_id="test-owner",
        approval_required=approval_required,
    )
    brain.recommendations = [
        {
            "id": "rec-1",
            "title": "Test recommendation",
            "rationale": "Test rationale",
            "evidence": [],
            "confidence": 0.8,
            "status": "pending_approval" if approval_required else "approved",
            "approvalRequired": approval_required,
            "executionStatus": "ready_for_execution_integration",
        }
    ]
    return brain


@pytest.mark.asyncio
async def test_unit_execute_without_approval_raises():
    """execute_action must reject unapproved recommendations."""
    service = SecondBrainService()
    brain = _make_brain(approval_required=True)
    with pytest.raises(PermissionError, match="requires approval"):
        await service.execute_action(brain, "rec-1")


@pytest.mark.asyncio
async def test_unit_execute_rejected_raises():
    """execute_action must reject already-rejected recommendations."""
    service = SecondBrainService()
    brain = _make_brain(approval_required=True)
    await service.reject_action(brain, "rec-1")
    with pytest.raises(PermissionError, match="rejected"):
        await service.execute_action(brain, "rec-1")


@pytest.mark.asyncio
async def test_unit_execute_twice_raises():
    """Second execute_action call must be blocked."""
    service = SecondBrainService(mission_registry=MissionRegistry())
    brain = _make_brain(approval_required=True)
    await service.approve(brain, "rec-1")
    result1 = await service.execute_action(brain, "rec-1")
    assert result1["executionStatus"] == "executed"
    with pytest.raises(PermissionError, match="already executed"):
        await service.execute_action(brain, "rec-1")


@pytest.mark.asyncio
async def test_unit_approve_rejected_raises():
    """approve() must not allow re-approving a rejected recommendation."""
    service = SecondBrainService()
    brain = _make_brain(approval_required=True)
    await service.reject_action(brain, "rec-1")
    with pytest.raises(PermissionError, match="not pending"):
        await service.approve(brain, "rec-1")


@pytest.mark.asyncio
async def test_unit_reject_approved_raises():
    """reject_action() must not allow rejecting an already-approved recommendation."""
    service = SecondBrainService()
    brain = _make_brain(approval_required=True)
    await service.approve(brain, "rec-1")
    with pytest.raises(PermissionError, match="not pending"):
        await service.reject_action(brain, "rec-1")


@pytest.mark.asyncio
async def test_unit_reject_executed_raises():
    """reject_action() must not allow rejecting an already-executed recommendation."""
    service = SecondBrainService(mission_registry=MissionRegistry())
    brain = _make_brain(approval_required=True)
    await service.approve(brain, "rec-1")
    await service.execute_action(brain, "rec-1")
    with pytest.raises(PermissionError, match="not pending"):
        await service.reject_action(brain, "rec-1")


@pytest.mark.asyncio
async def test_unit_concurrent_execute_only_one_succeeds():
    """Two simultaneous execute calls must not both succeed."""
    service = SecondBrainService(mission_registry=MissionRegistry())
    brain = _make_brain(approval_required=True)
    await service.approve(brain, "rec-1")

    results = await asyncio.gather(
        service.execute_action(brain, "rec-1"),
        service.execute_action(brain, "rec-1"),
        return_exceptions=True,
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
    assert len(failures) == 1
    assert isinstance(failures[0], PermissionError)


@pytest.mark.asyncio
async def test_unit_execute_sets_status_to_executed():
    """After successful execution, recommendation status must be 'executed'."""
    service = SecondBrainService(mission_registry=MissionRegistry())
    brain = _make_brain(approval_required=True)
    await service.approve(brain, "rec-1")
    await service.execute_action(brain, "rec-1")
    assert brain.recommendations[0]["status"] == "executed"
    assert brain.recommendations[0]["executionStatus"] == "executed"


@pytest.mark.asyncio
async def test_unit_truthful_no_agents_result():
    """When no agents/workflows attached, result must say so truthfully."""
    service = SecondBrainService(mission_registry=MissionRegistry())
    brain = _make_brain(approval_required=True)
    await service.approve(brain, "rec-1")
    result = await service.execute_action(brain, "rec-1")
    assert "no agents or workflows to execute" in result["executionResult"]


# ── HTTP API-level tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_execute_without_approval_returns_403(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    resp = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/execute"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_api_execute_rejected_returns_403(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/reject")
    resp = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/execute"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_api_execute_twice_returns_403(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    first = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/execute"
    )
    assert first.status_code == 200
    second = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/execute"
    )
    assert second.status_code == 403
    assert "already executed" in second.json()["detail"]


@pytest.mark.asyncio
async def test_api_approve_rejected_returns_403(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/reject")
    resp = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/approve"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_api_reject_after_approve_returns_403(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    resp = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/reject"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_api_reject_after_execute_returns_403(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/execute")
    resp = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/reject"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_api_cross_owner_execute_returns_404(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    other_login = await client.post(
        "/api/auth/login", json={"email": "other-gov-user", "password": "password"}
    )
    client.headers = {"Authorization": f"Bearer {other_login.json()['token']}"}
    resp = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/execute"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_cross_owner_approve_returns_404(client: AsyncClient):
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    other_login = await client.post(
        "/api/auth/login", json={"email": "other-gov-user", "password": "password"}
    )
    client.headers = {"Authorization": f"Bearer {other_login.json()['token']}"}
    resp = await client.post(
        f"/api/brains/{brain_id}/recommendations/{rec_id}/approve"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_execution_persists_state(client: AsyncClient):
    """After execution, the brain endpoint should reflect execution state."""
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/execute")

    brain = (await client.get(f"/api/brains/{brain_id}")).json()
    rec = brain["recommendations"][0]
    assert rec["status"] == "executed"
    assert rec["executionStatus"] in ("executed", "ready_for_integration")
    assert rec["executionResult"]
    assert rec["missionId"]


@pytest.mark.asyncio
async def test_api_execution_activity_provenance(client: AsyncClient):
    """Activity log must contain structured execution provenance."""
    brain_id, rec_id = await _create_brain_with_rec(client, approval_required=True)
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/approve")
    await client.post(f"/api/brains/{brain_id}/recommendations/{rec_id}/execute")

    activity = (await client.get(f"/api/brains/{brain_id}/activity")).json()
    actions = [entry["action"] for entry in activity]
    assert "recommendation_generated" in actions
    assert "approval_granted" in actions
    assert "action_executed" in actions or "action_ready_for_integration" in actions
    assert "memory_recorded" in actions