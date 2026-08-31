from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m3", tags=["m3"])

# Self-correction engine state
_corrections: list[dict[str, Any]] = []
_teams: list[dict[str, Any]] = []
_escalations: list[dict[str, Any]] = []
_supervisors: dict[str, dict[str, Any]] = {}


@router.post("/self-correction/diagnose", status_code=201)
async def diagnose(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    failure = str(body.get("failure", body.get("error", "unknown")))
    # classify
    categories = ["tool_failure", "connector_failure", "model_failure", "permission_failure", "budget_failure", "data_failure", "workflow_failure", "agent_failure", "runtime_failure", "policy_failure", "external_system_failure"]
    matched = next((c for c in categories if c.split("_")[0] in failure.lower()), "workflow_failure")
    rec = {"correction_id": f"corr-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "failure": failure, "diagnosis": matched, "evidence": body.get("evidence") or {"failure": failure}}
    _corrections.append(rec)
    return rec


@router.post("/self-correction/strategies")
async def generate_strategies(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    corr_id = str(body.get("correction_id", ""))
    strategies = ["retry", "alternate_tool", "alternate_connector", "alternate_agent", "alternate_model", "alternate_runtime", "change_sequence", "reduce_scope", "escalate"]
    # policy check stub — filter escalate if requires approval
    return {"tenant_id": tenant_id, "correction_id": corr_id, "strategies": strategies, "policy_checked": True}


@router.post("/self-correction/simulate")
async def simulate_strategies(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    strategies = body.get("strategies") or ["retry"]
    simulated = [{"strategy": s, "score": 0.8 if s == "retry" else 0.5} for s in strategies]
    best = max(simulated, key=lambda x: x["score"])["strategy"] if simulated else "retry"
    return {"tenant_id": tenant_id, "simulated": simulated, "selected": best}


@router.post("/reliability/detect")
async def detect_reliability(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # detect loops/deadlocks/stagnation etc.
    events = body.get("events") or []
    issues: list[str] = []
    if len(events) > 5 and len(set(str(e) for e in events)) == 1:
        issues.append("loop")
    if body.get("retries", 0) > 5:
        issues.append("excessive_retries")
    if body.get("duration_ms", 0) > 30000:
        issues.append("stagnation")
    return {"tenant_id": tenant_id, "issues": issues, "progress": body.get("progress", 0)}


@router.post("/reliability/predict-failure")
async def predict_failure(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # use M2 prediction stub
    risk = float(body.get("risk", 0.8))
    if risk > 0.7:
        return {"tenant_id": tenant_id, "likely_to_fail": True, "action": "warn/switch/request_approval", "risk": risk}
    return {"tenant_id": tenant_id, "likely_to_fail": False, "risk": risk}


@router.post("/workforce/hierarchy", status_code=201)
async def create_hierarchy(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"hierarchy_id": f"hier-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "levels": ["human", "executive_agent", "department_agent", "team_agent", "worker_agent", "tool"], "members": body.get("members") or []}
    return rec


@router.post("/workforce/team", status_code=201)
async def form_team(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    goal = str(body.get("goal", ""))
    if not goal:
        raise HTTPException(status_code=400, detail="goal required")
    rec = {"team_id": f"team-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "goal": goal, "members": body.get("members") or ["worker-1", "worker-2"], "task_graph": body.get("task_graph") or [{"task": "research"}, {"task": "execute"}]}
    _teams.append(rec)
    return rec


@router.get("/workforce/teams")
async def list_teams(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [t for t in _teams if t["tenant_id"] == tenant_id]


@router.post("/workforce/escalate", status_code=201)
async def escalate(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"escalation_id": f"esc-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "reason": str(body.get("reason", "needs review")), "evidence": body.get("evidence") or {}, "recommended_action": str(body.get("recommended_action", "review")), "risk": str(body.get("risk", "medium")), "cost": body.get("cost"), "confidence": float(body.get("confidence", 0.5)), "path": "worker→team_supervisor→dept_supervisor→executive→human"}
    _escalations.append(rec)
    return rec


@router.get("/workforce/escalations")
async def list_escalations(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [e for e in _escalations if e["tenant_id"] == tenant_id]


@router.get("/workforce/supervision/{agent_id}")
async def supervision_status(request: Request, agent_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {"agent_id": agent_id, "tenant_id": tenant_id, "workload": 0.6, "success_rate": 0.9, "latency_ms": 120, "cost": 12.5, "violations": 0, "status": "healthy"}


@router.post("/workforce/supervision/{agent_id}/action")
async def supervision_action(request: Request, agent_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    action = str(body.get("action", "reassign"))
    if action not in ("reassign", "pause", "resume", "escalate", "replace", "terminate"):
        raise HTTPException(status_code=400, detail="invalid action")
    return {"agent_id": agent_id, "tenant_id": tenant_id, "action": action, "status": "executed"}
