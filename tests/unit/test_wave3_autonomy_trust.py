from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.http.api import create_app
from eaip.auth.auth_providers import AuthenticationService


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
async def test_mcp_and_external_integrations_tenant_isolation():
    app, lc = await _make_app()
    apex, nova = await _tokens(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/integrations/servers", json={"name": "Apex MCP", "transport_type": "stdio", "command": "mock"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200, r.text
        sid = r.json()["server_id"]
        r = await client.get("/api/integrations/servers", headers={"Authorization": f"Bearer {nova}"})
        assert all(s["server_id"] != sid for s in r.json())
        # external ERP invoke
        r = await client.post("/api/external/erp/invoke", json={"tool": "orders", "args": {}}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["category"] == "erp"
        # cross-system workflow idempotent
        r = await client.post("/api/external/cross-system", json={"flow": "crm→erp", "idempotency_key": "idem-1"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["idempotency_key"] == "idem-1"
    await lc.stop()


@pytest.mark.asyncio
async def test_swarm_planning_and_consensus():
    app, lc = await _make_app()
    apex, _ = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/swarms/plan", json={"goal": "Analyze Q1 results", "capabilities": ["analysis", "strategy"]}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["count"] >= 1
        r = await client.post("/api/swarms", json={"name": "Test Swarm", "pattern": "parallel", "autonomy_level": "SUGGEST", "tasks": [{"task_id": "t1", "description": "Do A"}, {"task_id": "t2", "description": "Do B", "dependencies": ["t1"]}]}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        sid = r.json()["swarm_id"]
        r = await client.post(f"/api/swarms/{sid}/execute", json={}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["status"] in ("completed", "failed")
        assert "consensus" in r.json()
    await lc.stop()


@pytest.mark.asyncio
async def test_long_missions_recovery():
    app, lc = await _make_app()
    apex, _ = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/long-missions", json={"name": "Mission 1", "steps": [{"id": "s1"}, {"id": "s2"}]}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        mid = r.json()["mission_id"]
        r = await client.post(f"/api/long-missions/{mid}/checkpoint", json={"state": "half"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        r = await client.post(f"/api/long-missions/{mid}/recover", headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["status"] == "running"
        r = await client.post(f"/api/long-missions/{mid}/escalate", json={"reason": "manual"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
    await lc.stop()


@pytest.mark.asyncio
async def test_autonomy_and_workflow_compose():
    app, lc = await _make_app()
    apex, _ = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/autonomy/policies", json={"name": "Strict", "max_level": "L2", "max_budget": 500, "require_approval_for": ["external_write"]}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        pid = r.json()["policy_id"]
        r = await client.post("/api/autonomy/evaluate", json={"action": "external_write", "tool": "x", "risk": "high", "budget": 600, "level": "L4"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["decision"] in ("deny", "require_approval")
        r = await client.post("/api/workflow-compose/compose", json={"goal": "Research opportunity; Draft proposal"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and "workflow" in r.json()
        r = await client.post("/api/workflow-compose/validate", json=r.json()["workflow"], headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["valid"] is True
    await lc.stop()


@pytest.mark.asyncio
async def test_marketplace_signed_and_audit_verifiable():
    app, lc = await _make_app()
    apex, nova = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/marketplace-trusted/publish", json={"name": "Signed Pack", "type": "tool", "version": "1.0.0"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        pkg_id = r.json()["package_id"]
        r = await client.get(f"/api/marketplace-trusted/packages/{pkg_id}/verify", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["valid"] is True
        r = await client.post(f"/api/marketplace-trusted/packages/{pkg_id}/install", headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        r = await client.post(f"/api/marketplace-trusted/packages/{pkg_id}/revoke", headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        r = await client.post(f"/api/marketplace-trusted/packages/{pkg_id}/install", headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 400
        # audit verifiable
        r = await client.post("/api/audit-chain/execution", json={"execution_id": "exec-1", "inputs": "hello", "policy": "p1"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        rid = r.json()["record_id"]
        r = await client.get(f"/api/audit-chain/verify/{rid}", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["valid"] is True
        # nova isolation
        r = await client.get("/api/audit-chain", headers={"Authorization": f"Bearer {nova}"})
        assert all(rec["record_id"] != rid for rec in r.json())
    await lc.stop()


@pytest.mark.asyncio
async def test_federation_deny_and_delegation():
    app, lc = await _make_app()
    apex, _ = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/federation/orgs", json={"name": "Org A"}, headers={"Authorization": f"Bearer {apex}"})
        org_a = r.json()["org_id"]
        r = await client.post("/api/federation/orgs", json={"name": "Org B"}, headers={"Authorization": f"Bearer {apex}"})
        org_b = r.json()["org_id"]
        r = await client.post("/api/federation/check-access", json={"requester_org": org_a, "target_org": org_b}, headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["allowed"] is False
        r = await client.post("/api/federation/trusts", json={"from_org": org_a, "to_org": org_b}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        r = await client.post("/api/federation/check-access", json={"requester_org": org_a, "target_org": org_b}, headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["allowed"] is True
        r = await client.post("/api/federation/delegations", json={"who": "user1", "what": "read", "purpose": "audit", "ttl_seconds": 3600}, headers={"Authorization": f"Bearer {apex}"})
        did = r.json()["delegation_id"]
        r = await client.get(f"/api/federation/delegations/{did}", headers={"Authorization": f"Bearer {apex}"})
        assert r.json()["valid"] is True
    await lc.stop()


@pytest.mark.asyncio
async def test_advanced_simulation_branch_mc_and_control_plane():
    app, lc = await _make_app()
    apex, _ = await _tokens(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/simulation2/scenarios", json={"name": "base", "baseline_state": {"workload": 0.5}}, headers={"Authorization": f"Bearer {apex}"})
        sid = r.json()["scenario_id"]
        r = await client.post(f"/api/simulation2/scenarios/{sid}/branch", json={"name": "branch 1"}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 201
        branch_id = r.json()["scenario_id"]
        r = await client.post(f"/api/simulation2/scenarios/{branch_id}/monte-carlo", json={"runs": 5}, headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["runs"] == 5
        r = await client.get(f"/api/simulation2/scenarios/{branch_id}/sensitivity?param=cost", headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200
        r = await client.get("/api/control-plane/summary", headers={"Authorization": f"Bearer {apex}"})
        assert r.status_code == 200 and r.json()["tenant_id"] == "apex"
    await lc.stop()
