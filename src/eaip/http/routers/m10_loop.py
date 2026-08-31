"""M10 Full Autonomous Enterprise Loop — master loop, objective loop, autonomy, proof, HITL, scenarios, control plane."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.enterprise_loop.engine import EnterpriseLoopEngine, ObjectiveLoopEngine, StrategicCorrectionEngine
from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m10", tags=["m10-loop"])


def _loop(req: Request) -> EnterpriseLoopEngine:
    e = req.app.state.lifecycle.platform.container.try_resolve(EnterpriseLoopEngine)
    if e is None:
        e = EnterpriseLoopEngine(event_bus=req.app.state.lifecycle.platform.events if hasattr(req.app.state.lifecycle.platform, "events") else None)
        req.app.state.lifecycle.platform.container.register_instance(EnterpriseLoopEngine, e)
    return e


def _obj(req: Request) -> ObjectiveLoopEngine:
    e = req.app.state.lifecycle.platform.container.try_resolve(ObjectiveLoopEngine)
    if e is None:
        e = ObjectiveLoopEngine()
        req.app.state.lifecycle.platform.container.register_instance(ObjectiveLoopEngine, e)
    return e


def _corr(req: Request) -> StrategicCorrectionEngine:
    e = req.app.state.lifecycle.platform.container.try_resolve(StrategicCorrectionEngine)
    if e is None:
        e = StrategicCorrectionEngine()
        req.app.state.lifecycle.platform.container.register_instance(StrategicCorrectionEngine, e)
    return e


# Master enterprise loop — M10-A
@router.post("/loop")
async def create_loop(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    loop = _loop(request).create(tenant_id, objective=str(body.get("objective", body.get("goal", ""))), autonomy_level=str(body.get("autonomy_level", body.get("autonomy", "L2"))))
    return loop.model_dump(mode="json")


@router.get("/loop")
async def list_loops(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [r.model_dump(mode="json") for r in _loop(request).list_for_tenant(tenant_id)]


@router.get("/loop/{run_id}")
async def get_loop(request: Request, run_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    r = _loop(request).get(run_id, tenant_id)
    if not r:
        raise HTTPException(status_code=404, detail="loop not found")
    return r.model_dump(mode="json")


@router.post("/loop/{run_id}/advance")
async def advance_loop(request: Request, run_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    r = _loop(request).advance(run_id, tenant_id, data=body)
    if not r:
        raise HTTPException(status_code=404, detail="loop not found")
    return r.model_dump(mode="json")


@router.post("/loop/{run_id}/approve")
async def approve_loop(request: Request, run_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    approver = str((body or {}).get("approver", _user.get("sub", "unknown")))
    r = _loop(request).approve(run_id, tenant_id, approver=approver)
    if not r:
        raise HTTPException(status_code=404, detail="loop not found or not awaiting approval")
    return r.model_dump(mode="json")


@router.post("/loop/{run_id}/cancel")
async def cancel_loop(request: Request, run_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    r = _loop(request).cancel(run_id, tenant_id)
    if not r:
        raise HTTPException(status_code=404, detail="loop not found")
    return r.model_dump(mode="json")


@router.post("/loop/{run_id}/check-autonomy")
async def check_autonomy(request: Request, run_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _loop(request)
    run = eng.get(run_id, tenant_id)
    if not run:
        raise HTTPException(status_code=404, detail="loop not found")
    result = eng.check_autonomy(run, action=str(body.get("action", "")), risk=str(body.get("risk", "low")), cost=float(body.get("cost", 0)), budget=float(body.get("budget", 10000)))
    return result.model_dump(mode="json")


# Objective loop — M10-B
@router.post("/objective")
async def create_objective(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    obj = str(body.get("objective", body.get("goal", "")))
    if not obj:
        raise HTTPException(status_code=400, detail="objective is required")
    run = _obj(request).create(tenant_id, objective=obj)
    if body.get("context"):
        run.context = dict(body["context"])
    return run.model_dump(mode="json")


@router.get("/objective")
async def list_objectives(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [r.model_dump(mode="json") for r in _obj(request).list_for_tenant(tenant_id)]


@router.get("/objective/{run_id}")
async def get_objective(request: Request, run_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    r = _obj(request).get(run_id, tenant_id)
    if not r:
        raise HTTPException(status_code=404, detail="objective not found")
    return r.model_dump(mode="json")


@router.post("/objective/{run_id}/advance")
async def advance_objective(request: Request, run_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    r = _obj(request).advance(run_id, tenant_id, data=body)
    if not r:
        raise HTTPException(status_code=404, detail="objective not found")
    return r.model_dump(mode="json")


# Self-correction — M10-D
@router.post("/correction")
async def create_correction(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    sc = _corr(request).create(tenant_id, expected=dict(body.get("expected", {})), actual=dict(body.get("actual", {})))
    return sc.model_dump(mode="json")


@router.get("/correction/{correction_id}")
async def get_correction(request: Request, correction_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    c = _corr(request).get(correction_id, tenant_id)
    if not c:
        raise HTTPException(status_code=404, detail="correction not found")
    return c.model_dump(mode="json")


# Enterprise proof — M10-F
@router.get("/loop/{run_id}/proof")
async def loop_proof(request: Request, run_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    run = _loop(request).get(run_id, tenant_id)
    if not run:
        raise HTTPException(status_code=404, detail="loop not found")
    return {"run_id": run_id, "tenant_id": tenant_id, "proof_refs": run.proof_refs, "phases_completed": run.phases_completed, "status": run.status.value, "current_phase": run.current_phase.value}


# Scenarios — M10-H
@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(request: Request, scenario_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    scenarios = {
        "apex-customer-intelligence": {"enterprise": "Apex Advisory Group", "flow": "objective→customer intelligence→opportunity→strategy→simulation→governance→workforce→CRM→campaign→KPI→learning→strategy update", "synthetic": True},
        "nova-production": {"enterprise": "Nova Manufacturing Systems", "flow": "production objective→events→prediction→failure prevention→SCADA/ERP→recovery→KPI→learning", "synthetic": True},
        "meridian-healthcare": {"enterprise": "Meridian Health Services", "flow": "healthcare objective→EHR context→policy→model routing→governance→approval→workflow→outcome→audit→learning", "synthetic": True},
    }
    sc = scenarios.get(scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"scenario {scenario_id!r} not found — available: {list(scenarios.keys())}")
    # create a loop run for the scenario
    loop = _loop(request).create(tenant_id, objective=f"scenario:{scenario_id}", autonomy_level="L2")
    return {"scenario_id": scenario_id, "loop_id": loop.run_id, **sc, "loop": loop.model_dump(mode="json")}


# Control plane — M10-I
@router.get("/control-plane")
async def control_plane(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    loops = _loop(request).list_for_tenant(tenant_id)
    objectives = _obj(request).list_for_tenant(tenant_id)
    return {
        "tenant_id": tenant_id,
        "strategy": "via /api/m10/loop and /api/m10/objective",
        "intelligence": f"{len(loops)} loops, {len(objectives)} objectives",
        "missions": "see /api/long-missions",
        "workflows": "see /api/workflows",
        "workforce": "see /api/workforce",
        "models": "see /api/m2/intelligence — predictions + routing",
        "connectors": "see /api/integrations",
        "governance": "see /api/governance2",
        "audit": f"{len(loops)} proof refs available",
        "costs": "see /api/cost_v2",
        "health": "see /m8/operations/center",
        "predictions": "see /api/m2/intelligence",
        "learning": "see M5 learning records",
        "loops": [r.model_dump(mode="json") for r in loops[:5]],
    }
