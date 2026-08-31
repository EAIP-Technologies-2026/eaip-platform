from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.auth.auth_providers import AuthenticationService
from eaip.http.api import create_app


async def _make_app():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()
    c = lifecycle.platform.container
    e = lifecycle.platform.events
    c.register_instance(AuthenticationService, AuthenticationService(secret="test-secret", event_bus=e))
    app = create_app(lifecycle)
    return app, lifecycle


async def _tokens(app):
    auth: AuthenticationService = app.state.lifecycle.platform.container.resolve(AuthenticationService)
    from eaip.auth.auth_providers import AuthenticationRequest
    from eaip.auth.models import TokenType

    async def _tok(sub: str, org: str) -> str:
        req = AuthenticationRequest(id=f"req-{sub}", provider="mock", credentials={"username": sub, "password": "valid"})
        res = await auth.authenticate(req)
        assert res.success
        auth._identity_store.add(sub, {"sub": sub, "organization_id": org, "roles": ["admin"], "name": sub})
        tok = await auth.token_service.create_token(subject=sub, type=TokenType.ACCESS, claims={"sub": sub, "organization_id": org, "roles": ["admin"]})
        s = await auth.token_service.get_token_string(tok.id)
        assert s
        return s

    return await _tok("apex-user", "apex"), await _tok("nova-user", "nova")


@pytest.mark.asyncio
async def test_observability_timeline():
    app, lc = await _make_app()
    apex, _ = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/observability/events", json={"action": "test_action", "resource": "agent", "correlation_id": "corr-1", "metadata": {"secret_token": "should_be_filtered"}}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        cid = r.json()["correlation_id"]
        assert "secret_token" not in str(r.json())
        r = await client.get(f"/api/observability/timeline/{cid}", headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["count"] >= 1
    await lc.stop()


@pytest.mark.asyncio
async def test_cost_v2_tenant_isolation():
    app, lc = await _make_app()
    apex, nova = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/cost-v2/record", json={"category": "ai", "amount": 12.5}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        r = await client.get("/api/cost-v2/summary", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["total"] >= 12.5
        r = await client.get("/api/cost-v2/summary", headers={"Authorization": f"Bearer {nova}"})
        assert r.json()["total"] == 0
        r = await client.post("/api/cost-v2/budgets", json={"name": "apex budget", "amount": 10}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        bid = r.json()["id"]
        r = await client.post("/api/cost-v2/check-budget", json={"budget_id": bid, "estimated_cost": 20}, headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["requires_approval"] is True
    await lc.stop()


@pytest.mark.asyncio
async def test_health_incidents_and_deployment():
    app, lc = await _make_app()
    apex, nova = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/health-center/incidents", json={"title": "DB degraded", "severity": "critical"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        iid = r.json()["incident_id"]
        r = await client.get("/api/health-center/incidents", headers={"Authorization": f"Bearer {nova}"})
        assert all(i["incident_id"] != iid for i in r.json())
        r = await client.post(f"/api/health-center/incidents/{iid}/acknowledge", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["status"] == "acknowledged"
        r = await client.get("/api/deployment/checklist", headers={"Authorization": f"Bearer {apex}"})
        assert "human_required" in str(r.json())
    await lc.stop()


@pytest.mark.asyncio
async def test_kpi_and_feature_flags_and_approvals():
    app, lc = await _make_app()
    apex, _ = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/kpi", json={"name": "Revenue", "goal": "grow 10%", "target": 100, "actual": 60}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        r = await client.get("/api/kpi/outcome", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["count"] >= 1
        r = await client.put("/api/feature-flags/flag-1", json={"enabled": True, "rollout_pct": 50}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        r = await client.get("/api/feature-flags/flag-1/check", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["enabled"] is True
        r = await client.post("/api/approval-center", json={"title": "Approve budget"}, headers={"Authorization": f"Bearer {apex}"})
        aid = r.json()["approval_id"]
        r = await client.post(f"/api/approval-center/{aid}/approve", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["status"] == "approved"
    await lc.stop()
