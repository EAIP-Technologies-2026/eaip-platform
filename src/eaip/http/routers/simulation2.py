from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.simulation.scenario_service import ScenarioEngine
from eaip.simulation.twin import TwinRegistry
from eaip.logging.context import get_logger

router = APIRouter(prefix="/simulation2", tags=["simulation2"])
log = get_logger("eaip.http.routers.simulation2")


def _scenario_engine(request: Request) -> ScenarioEngine:
    eng = request.app.state.lifecycle.platform.container.try_resolve(ScenarioEngine)
    if eng is None:
        eng = ScenarioEngine()
        try:
            request.app.state.lifecycle.platform.container.register_instance(ScenarioEngine, eng)
        except Exception:
            pass
    return eng


def _twin_registry(request: Request) -> TwinRegistry:
    reg = request.app.state.lifecycle.platform.container.try_resolve(TwinRegistry)
    if reg is None:
        reg = TwinRegistry()
        try:
            request.app.state.lifecycle.platform.container.register_instance(TwinRegistry, reg)
        except Exception:
            pass
    return reg


@router.post("/twins", status_code=201)
async def create_twin(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _twin_registry(request)
    enterprise = str(body.get("enterprise", "apex"))
    twin = reg.create(tenant_id=tenant_id, enterprise=enterprise, state=body.get("state"), workforce=body.get("workforce"), agents=body.get("agents"), processes=body.get("processes"), resources=body.get("resources"), suppliers=body.get("suppliers"), customers=body.get("customers"), inventory=body.get("inventory"), schedules=body.get("schedules"), financial=body.get("financial"), kpis=body.get("kpis"), risk=body.get("risk"))
    return twin.model_dump(mode="json")


@router.get("/twins")
async def list_twins(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    reg = _twin_registry(request)
    return [t.model_dump(mode="json") for t in reg.list_for_tenant(tenant_id)]


@router.get("/twins/{twin_id}")
async def get_twin(request: Request, twin_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _twin_registry(request)
    twin = reg.get(twin_id, tenant_id)
    if not twin:
        raise HTTPException(status_code=404, detail="twin not found")
    return twin.model_dump(mode="json")


@router.patch("/twins/{twin_id}")
async def update_twin(request: Request, twin_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _twin_registry(request)
    updated = reg.update(twin_id, tenant_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail="twin not found")
    return updated.model_dump(mode="json")


@router.delete("/twins/{twin_id}")
async def delete_twin(request: Request, twin_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _twin_registry(request)
    if not reg.delete(twin_id, tenant_id):
        raise HTTPException(status_code=404, detail="twin not found")
    return {"status": "deleted", "twin_id": twin_id}


@router.post("/scenarios", status_code=201)
async def create_scenario(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    name = str(body.get("name") or body.get("scenario_name") or f"scenario-{uuid.uuid4().hex[:6]}")
    baseline = body.get("baseline_state") or body.get("baselineState") or body.get("baseline") or {}
    if not isinstance(baseline, dict):
        raise HTTPException(status_code=400, detail="baseline_state must be an object")
    scenario_id = eng.create_scenario(tenant_id, baseline, name)
    scn = eng.get(scenario_id, tenant_id)
    assert scn is not None
    return {"scenario_id": scn.scenario_id, "tenant_id": scn.tenant_id, "name": scn.name, "baseline_state": scn.baseline_state, "alternatives": [a.model_dump(mode="json") for a in scn.alternatives], "steps": list(scn.steps), "created_at": scn.created_at}


@router.get("/scenarios")
async def list_scenarios(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    eng = _scenario_engine(request)
    return [{"scenario_id": s.scenario_id, "tenant_id": s.tenant_id, "name": s.name, "baseline_state": s.baseline_state, "alternatives": [a.model_dump(mode="json") for a in s.alternatives], "steps": list(s.steps), "created_at": s.created_at} for s in eng.list_for_tenant(tenant_id)]


@router.get("/scenarios/{scenario_id}")
async def get_scenario(request: Request, scenario_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    scn = eng.get(scenario_id, tenant_id)
    if not scn:
        raise HTTPException(status_code=404, detail="scenario not found")
    return {"scenario_id": scn.scenario_id, "tenant_id": scn.tenant_id, "name": scn.name, "baseline_state": scn.baseline_state, "alternatives": [a.model_dump(mode="json") for a in scn.alternatives], "steps": list(scn.steps), "created_at": scn.created_at}


@router.post("/scenarios/{scenario_id}/alternatives", status_code=201)
async def add_alternative(request: Request, scenario_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    intervention = body.get("intervention") or {}
    constraints = body.get("constraints") or {}
    if not isinstance(intervention, dict) or not isinstance(constraints, dict):
        raise HTTPException(status_code=400, detail="intervention and constraints must be objects")
    try:
        alt_id = eng.add_alternative(scenario_id, tenant_id, intervention, constraints)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    scn = eng.get(scenario_id, tenant_id)
    assert scn is not None
    alt = next((a for a in scn.alternatives if a.alt_id == alt_id), None)
    return {"alt_id": alt_id, "alternative": alt.model_dump(mode="json") if alt else {"alt_id": alt_id, "intervention": intervention, "constraints": constraints}}


@router.post("/scenarios/{scenario_id}/counterfactual")
async def run_counterfactual(request: Request, scenario_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    question = str(body.get("question") or body.get("what_if") or body.get("whatIf") or "what-if baseline")
    try:
        result = eng.run_counterfactual(scenario_id, tenant_id, question)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"scenario_id": scenario_id, "tenant_id": tenant_id, "question": question, **result}


@router.post("/scenarios/compare")
async def compare_scenarios(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    ids = body.get("scenario_ids") or body.get("scenarioIds") or body.get("ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail="scenario_ids list required")
    scenario_ids = [str(x) for x in ids]
    result = eng.compare(scenario_ids, tenant_id)
    return {"tenant_id": tenant_id, "comparison": result}


@router.post("/scenarios/{scenario_id}/branch", status_code=201)
async def branch_scenario(request: Request, scenario_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    name = str((body or {}).get("name", ""))
    try:
        new_id = eng.branch(scenario_id, tenant_id, name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"scenario_id": new_id, "from": scenario_id, "tenant_id": tenant_id}


@router.post("/scenarios/{scenario_id}/monte-carlo")
async def monte_carlo(request: Request, scenario_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    runs = int((body or {}).get("runs", 10))
    try:
        return eng.monte_carlo(scenario_id, tenant_id, runs=runs)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/scenarios/{scenario_id}/sensitivity")
async def sensitivity(request: Request, scenario_id: str, param: str = "cost", tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    try:
        return eng.sensitivity(scenario_id, tenant_id, param=param)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/scenarios/{scenario_id}/replay")
async def replay_scenario(request: Request, scenario_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _scenario_engine(request)
    try:
        steps = eng.replay(scenario_id, tenant_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"scenario_id": scenario_id, "tenant_id": tenant_id, "steps": steps, "count": len(steps)}


__all__ = ["router"]
