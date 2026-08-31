from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.autonomy.engine import AutonomyEngine
from eaip.autonomy.models import AutonomyLevel, AutonomyPolicy
from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/autonomy", tags=["autonomy"])


def _engine(req: Request) -> AutonomyEngine:
    eng = req.app.state.lifecycle.platform.container.try_resolve(AutonomyEngine)
    if eng is None:
        eng = AutonomyEngine()
        req.app.state.lifecycle.platform.container.register_instance(AutonomyEngine, eng)
    return eng


@router.post("/policies", status_code=201)
async def create_policy(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _engine(request)
    pid = str(body.get("policy_id") or body.get("policyId") or f"pol-{uuid.uuid4().hex[:8]}")
    level = str(body.get("max_level") or body.get("maxLevel") or "L1")
    try:
        lvl = AutonomyLevel(level)
    except ValueError:
        lvl = AutonomyLevel.L1_RECOMMEND
    pol = AutonomyPolicy(policy_id=pid, tenant_id=tenant_id, name=str(body.get("name", pid)), max_level=lvl, allowed_tools=tuple(body.get("allowed_tools") or body.get("allowedTools") or []), blocked_tools=tuple(body.get("blocked_tools") or body.get("blockedTools") or []), allowed_connectors=tuple(body.get("allowed_connectors") or body.get("allowedConnectors") or []), max_budget=float(body.get("max_budget") or body.get("maxBudget") or 1000), max_time_s=float(body.get("max_time_s") or body.get("maxTimeS") or 300), require_approval_for=tuple(body.get("require_approval_for") or body.get("requireApprovalFor") or []), metadata=body.get("metadata") or {})
    eng.put_policy(pol)
    return pol.model_dump(mode="json")


@router.get("/policies")
async def list_policies(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [p.model_dump(mode="json") for p in _engine(request).list_for_tenant(tenant_id)]


@router.get("/policies/{policy_id}")
async def get_policy(request: Request, policy_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    pol = _engine(request).get_policy(policy_id, tenant_id)
    if not pol:
        raise HTTPException(status_code=404, detail="policy not found")
    return pol.model_dump(mode="json")


@router.post("/evaluate")
async def evaluate(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _engine(request)
    return eng.evaluate(tenant_id, action=str(body.get("action", "execute")), tool=str(body.get("tool", "")), connector=str(body.get("connector", "")), risk=str(body.get("risk", "low")), budget=float(body.get("budget", 0)), level=str(body.get("level", "L2")))


@router.post("/policies/{policy_id}/evaluate")
async def evaluate_policy(request: Request, policy_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    eng = _engine(request)
    pol = eng.get_policy(policy_id, tenant_id)
    if not pol:
        raise HTTPException(status_code=404, detail="policy not found")
    return eng.evaluate(tenant_id, action=str(body.get("action", "execute")), tool=str(body.get("tool", "")), connector=str(body.get("connector", "")), risk=str(body.get("risk", "low")), budget=float(body.get("budget", 0)), level=str(body.get("level", "L2")))
