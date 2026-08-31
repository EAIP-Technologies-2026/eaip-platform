from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from eaip.app.builder import ApplicationBuilder
from eaip.http.api import create_app
from eaip.auth.auth_providers import AuthenticationService
from eaip.workforce.digital_service import DigitalWorkforceService
from eaip.methodology.registry import MethodologyRegistry
from eaip.document_intelligence.engine import DocumentIntelligenceEngine
from eaip.simulation.scenario_service import ScenarioEngine
from eaip.simulation.twin import TwinRegistry
from eaip.ops_intelligence.service import OpsIntelligenceService
from eaip.improvement.service import ImprovementService
from eaip.intelligence.decision_service import DecisionIntelligenceService
from eaip.intelligence.registry import CapabilityRegistry
from eaip.intelligence.kernel import IntelligenceKernel


async def _make_app():
    builder = ApplicationBuilder()
    lifecycle = builder.build()
    await lifecycle.start()
    c = lifecycle.platform.container
    e = lifecycle.platform.events
    # auth
    c.register_instance(AuthenticationService, AuthenticationService(secret="test-secret", event_bus=e))
    # wave2 services
    c.register_instance(DigitalWorkforceService, DigitalWorkforceService(event_bus=e))
    c.register_instance(MethodologyRegistry, MethodologyRegistry())
    c.register_instance(DocumentIntelligenceEngine, DocumentIntelligenceEngine())
    c.register_instance(ScenarioEngine, ScenarioEngine())
    c.register_instance(TwinRegistry, TwinRegistry())
    c.register_instance(OpsIntelligenceService, OpsIntelligenceService())
    c.register_instance(ImprovementService, ImprovementService())
    dec = DecisionIntelligenceService(simulation_engine=ScenarioEngine())
    c.register_instance(DecisionIntelligenceService, dec)
    cap_reg = CapabilityRegistry()
    c.register_instance(CapabilityRegistry, cap_reg)
    c.register_instance(IntelligenceKernel, IntelligenceKernel(registry=cap_reg, event_bus=e))
    app = create_app(lifecycle)
    return app, lifecycle


async def _auth_client(app):
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    # use the app's auth service to create proper tokens (stored in token store)
    auth_svc: AuthenticationService = app.state.lifecycle.platform.container.resolve(AuthenticationService)
    from eaip.auth.auth_providers import AuthenticationRequest
    # login via mock provider — then patch tenant/roles via direct token creation with claims
    # Simpler: authenticate then override claims via token service directly
    # Create tokens by calling authenticate with known users
    async def _token_for(sub: str, org: str) -> str:
        req = AuthenticationRequest(id=f"req-{sub}", provider="mock", credentials={"username": sub, "password": "valid"})
        res = await auth_svc.authenticate(req)
        assert res.success and res.token, res.error
        # patch identity to include requested org/roles so get_current_user returns them
        auth_svc._identity_store.add(sub, {"sub": sub, "organization_id": org, "roles": ["admin"], "name": sub})
        # also need claims in token to carry org — re-create token with org claim
        from eaip.auth.models import TokenType
        tok = await auth_svc.token_service.create_token(subject=sub, type=TokenType.ACCESS, claims={"sub": sub, "organization_id": org, "roles": ["admin"]})
        tok_str = await auth_svc.token_service.get_token_string(tok.id)
        assert tok_str
        return tok_str
    tok_apex = await _token_for("apex-user", "apex")
    tok_nova = await _token_for("nova-user", "nova")
    return client, tok_apex, tok_nova


@pytest.mark.asyncio
async def test_workforce_employee_lifecycle_and_isolation():
    app, lc = await _make_app()
    client, tok_apex, tok_nova = await _auth_client(app)
    try:
        # create apex employee
        r = await client.post("/api/workforce2/employees", json={"name": "Apex Analyst", "role": "analyst", "skills": {"analysis": 0.9}}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201, r.text
        emp_id = r.json()["employee_id"]
        # list apex sees it
        r = await client.get("/api/workforce2/employees", headers={"Authorization": f"Bearer {tok_apex}"})
        assert any(e["employee_id"] == emp_id for e in r.json())
        # nova does NOT see it
        r = await client.get("/api/workforce2/employees", headers={"Authorization": f"Bearer {tok_nova}"})
        assert all(e["employee_id"] != emp_id for e in r.json())
        # get by id cross-tenant fails
        r = await client.get(f"/api/workforce2/employees/{emp_id}", headers={"Authorization": f"Bearer {tok_nova}"})
        assert r.status_code == 404
        # capacity tenant-scoped
        r = await client.get("/api/workforce2/capacity", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["total"] >= 1
        r = await client.get("/api/workforce2/capacity", headers={"Authorization": f"Bearer {tok_nova}"})
        assert r.json()["total"] == 0
        # skill matching
        r = await client.post("/api/workforce2/match", json={"task_requirements": {"analysis": 1.0}}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and len(r.json()) >= 1
        # assignments
        r = await client.post("/api/workforce2/assignments", json={"tasks": [{"task_requirements": {"analysis": 1.0}, "priority": 1}]}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        # performance
        r = await client.post(f"/api/workforce2/employees/{emp_id}/performance", json={"quality": 0.95}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
    finally:
        await client.aclose()
        await lc.stop()


@pytest.mark.asyncio
async def test_methodology_registry_tenant_isolation():
    app, lc = await _make_app()
    client, tok_apex, tok_nova = await _auth_client(app)
    try:
        r = await client.post("/api/methodologies", json={"name": "Risk Method", "category": "risk", "benchmark_score": 0.9}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        mid = r.json()["methodology_id"]
        r = await client.get("/api/methodologies", headers={"Authorization": f"Bearer {tok_apex}"})
        assert any(m["methodology_id"] == mid for m in r.json())
        r = await client.get("/api/methodologies", headers={"Authorization": f"Bearer {tok_nova}"})
        assert all(m["methodology_id"] != mid for m in r.json())
        r = await client.post("/api/methodologies/recommend", json={"category": "risk"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        r = await client.post(f"/api/methodologies/{mid}/evaluate", json={"reliability": 0.99}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["reliability"] == 0.99
    finally:
        await client.aclose()
        await lc.stop()


@pytest.mark.asyncio
async def test_document_intelligence_tenant_isolation():
    app, lc = await _make_app()
    client, tok_apex, tok_nova = await _auth_client(app)
    try:
        r = await client.post("/api/documents/intelligence/ingest", json={"source": "doc.txt", "content": "hello world | table"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200, r.text
        doc_id = r.json()["document_id"]
        r = await client.get(f"/api/documents/intelligence/{doc_id}", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        r = await client.get(f"/api/documents/intelligence/{doc_id}", headers={"Authorization": f"Bearer {tok_nova}"})
        assert r.status_code == 404
        r = await client.get(f"/api/documents/intelligence/{doc_id}/entities", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and "entities" in r.json()
        r = await client.post(f"/api/documents/intelligence/{doc_id}/validate", json={"classification": "validated"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["status"] == "validated"
    finally:
        await client.aclose()
        await lc.stop()


@pytest.mark.asyncio
async def test_governance2_tenant_isolation():
    app, lc = await _make_app()
    client, tok_apex, tok_nova = await _auth_client(app)
    try:
        r = await client.post("/api/governance2/systems", json={"name": "Apex Model", "type": "model", "risk": "high"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        sid = r.json()["system_id"]
        r = await client.get("/api/governance2/systems", headers={"Authorization": f"Bearer {tok_nova}"})
        assert all(s["system_id"] != sid for s in r.json())
        r = await client.get(f"/api/governance2/systems/{sid}", headers={"Authorization": f"Bearer {tok_nova}"})
        assert r.status_code == 404
        r = await client.post(f"/api/governance2/systems/{sid}/risk", json={"risk": "critical"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        r = await client.post("/api/governance2/policies", json={"name": "High risk gate", "risk_threshold": "high", "allowed_actions": ["execute"]}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        pid = r.json()["policy_id"]
        r = await client.post(f"/api/governance2/policies/{pid}/evaluate", json={"action": "execute", "risk": "critical"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["allowed"] is False
        r = await client.get(f"/api/governance2/explain/{sid}", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and "what" in r.json()
    finally:
        await client.aclose()
        await lc.stop()


@pytest.mark.asyncio
async def test_simulation2_and_decision_fusion():
    app, lc = await _make_app()
    client, tok_apex, _ = await _auth_client(app)
    try:
        # twins
        r = await client.post("/api/simulation2/twins", json={"enterprise": "apex", "kpis": {"utilization": 0.7}}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        twin_id = r.json()["twin_id"]
        r = await client.get(f"/api/simulation2/twins/{twin_id}", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        # scenarios
        r = await client.post("/api/simulation2/scenarios", json={"name": "apex scenario", "baseline_state": {"workload": 0.7}}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        scn_id = r.json()["scenario_id"]
        r = await client.post(f"/api/simulation2/scenarios/{scn_id}/alternatives", json={"intervention": {"add_capacity": 0.2}, "constraints": {}}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        r = await client.post(f"/api/simulation2/scenarios/{scn_id}/counterfactual", json={"question": "what if demand +25%?"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and "simulated_outcome" in r.json()
        assert "FACT" not in r.json() or True  # fact/assumption/simulated distinction via keys fact/assumption/simulated_outcome
        assert "fact" in r.json() and "assumption" in r.json() and "simulated_outcome" in r.json()
        r = await client.post("/api/simulation2/scenarios/compare", json={"scenario_ids": [scn_id]}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        r = await client.get(f"/api/simulation2/scenarios/{scn_id}/replay", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["count"] >= 1
        # decision fusion
        r = await client.post("/api/intelligence/decisions", json={"title": "Dec 1", "objective": "test fusion"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        did = r.json()["decision_id"]
        r = await client.post(f"/api/intelligence/decisions/{did}/alternatives", json={"alternatives": [{"name": "A", "cost": 1000, "risk": 0.2}, {"name": "B", "cost": 2000, "risk": 0.5}]}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        r = await client.post(f"/api/intelligence/decisions/{did}/simulate", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and "simulations" in r.json() and "predicted" in r.json()
        r = await client.post(f"/api/intelligence/decisions/{did}/evaluate", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and "recommendation" in r.json()
        r = await client.post(f"/api/intelligence/decisions/{did}/approve", json={"approver": "user-apex"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        r = await client.post(f"/api/intelligence/decisions/{did}/execute", json={}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        r = await client.post(f"/api/intelligence/decisions/{did}/review", json={"actual_outcome": "chose A and succeeded"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        # quality (predicted vs actual)
        from eaip.intelligence.decision_service import DecisionIntelligenceService
        dec_svc = app.state.lifecycle.platform.container.try_resolve(DecisionIntelligenceService)
        assert dec_svc is not None
        q = dec_svc.quality(did, "apex")
        assert "predicted" in q and "actual" in q and "calibration" in q
    finally:
        await client.aclose()
        await lc.stop()


@pytest.mark.asyncio
async def test_ops_intelligence_and_improvement_pipeline():
    app, lc = await _make_app()
    client, tok_apex, tok_nova = await _auth_client(app)
    try:
        # ingest events that trigger anomaly
        r = await client.post("/api/ops-intelligence/ingest", json={"events": [{"tenant_id": "apex", "latency": 1500, "system": "api"}]}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        r = await client.get("/api/ops-intelligence/insights", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200
        insights = r.json()
        assert len(insights) >= 1
        iid = insights[0]["insight_id"]
        r = await client.get("/api/ops-intelligence/insights", headers={"Authorization": f"Bearer {tok_nova}"})
        assert all(i["insight_id"] != iid for i in r.json())
        r = await client.post(f"/api/ops-intelligence/insights/{iid}/escalate", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["status"] == "escalated"
        # improvement lifecycle
        r = await client.post("/api/improvements", json={"problem": {"title": "latency spike"}, "source": "ops_intelligence"}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 201
        pid = r.json()["proposal_id"]
        assert r.json()["status"] == "simulated"
        r = await client.get("/api/improvements", headers={"Authorization": f"Bearer {tok_nova}"})
        assert all(p["proposal_id"] != pid for p in r.json())
        r = await client.post(f"/api/improvements/{pid}/review", json={"approved": True}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["status"] == "approved"
        r = await client.post(f"/api/improvements/{pid}/apply", headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["status"] == "deployed"
        r = await client.post(f"/api/improvements/{pid}/measure", json={"outcome": {"improved": True}}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and r.json()["status"] == "measured"
        # wave2 pipeline
        r = await client.post("/api/wave2/pipeline/run", json={"trigger": {"type": "anomaly", "goal": "reduce latency", "tasks": [{"task_requirements": {"analysis": 1.0}}]}}, headers={"Authorization": f"Bearer {tok_apex}"})
        assert r.status_code == 200 and "trace" in r.json()
    finally:
        await client.aclose()
        await lc.stop()
