from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.governance_center.models import GovernedSystem, GovernedSystemType, PolicyRecord, RiskAssessment, RiskLevel
from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger

router = APIRouter(prefix="/governance2", tags=["governance2"])
log = get_logger("eaip.http.routers.governance2")

_store: dict[str, GovernedSystem] = {}
_risk: dict[str, list[RiskAssessment]] = {}
_policies: dict[str, PolicyRecord] = {}


def _key(tenant_id: str, system_id: str) -> str:
    return f"{tenant_id}:{system_id}"


def _policy_key(tenant_id: str, policy_id: str) -> str:
    return f"{tenant_id}:{policy_id}"


def _to_dict(s: GovernedSystem) -> dict[str, Any]:
    return {
        "system_id": s.system_id,
        "systemId": s.system_id,
        "tenant_id": s.tenant_id,
        "type": s.type.value,
        "name": s.name,
        "version": s.version,
        "risk": s.risk.value,
        "owner": s.owner,
        "lifecycle": s.lifecycle,
        "approval": s.approval,
        "policy_status": s.policy_status,
        "policyStatus": s.policy_status,
        "description": s.description,
        "metadata": dict(s.metadata),
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


def _policy_to_dict(p: PolicyRecord) -> dict[str, Any]:
    return {
        "policy_id": p.policy_id,
        "policyId": p.policy_id,
        "tenant_id": p.tenant_id,
        "name": p.name,
        "description": p.description,
        "allowed_actions": list(p.allowed_actions),
        "allowedActions": list(p.allowed_actions),
        "risk_threshold": p.risk_threshold.value,
        "riskThreshold": p.risk_threshold.value,
        "enabled": p.enabled,
        "metadata": dict(p.metadata),
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.post("/systems", status_code=201)
async def create_system(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    system_id = str(body.get("system_id") or body.get("systemId") or f"gov-{uuid.uuid4().hex[:8]}")
    raw_type = str(body.get("type", "model"))
    try:
        gtype = GovernedSystemType(raw_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid type {raw_type!r}") from None
    raw_risk = str(body.get("risk", "low"))
    try:
        risk = RiskLevel(raw_risk.lower())
    except ValueError:
        risk = RiskLevel.low
    key = _key(tenant_id, system_id)
    if key in _store:
        raise HTTPException(status_code=409, detail=f"system {system_id!r} already exists")
    rec = GovernedSystem(system_id=system_id, tenant_id=tenant_id, type=gtype, name=str(body.get("name") or system_id), version=str(body.get("version", "1.0.0")), risk=risk, owner=str(body.get("owner", "")), lifecycle=str(body.get("lifecycle", "draft")), approval=str(body.get("approval", "pending")), policy_status=str(body.get("policy_status") or body.get("policyStatus") or "pending"), description=str(body.get("description", "")), metadata=body.get("metadata") or {})
    _store[key] = rec
    log.info("governance2.system_created", system_id=system_id, tenant_id=tenant_id)
    return _to_dict(rec)


@router.get("/systems")
async def list_systems(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), type: str | None = None, risk: str | None = None, lifecycle: str | None = None) -> list[dict[str, Any]]:
    prefix = f"{tenant_id}:"
    results = [v for k, v in _store.items() if k.startswith(prefix)]
    if type:
        results = [r for r in results if r.type.value == type.lower()]
    if risk:
        results = [r for r in results if r.risk.value == risk.lower()]
    if lifecycle:
        results = [r for r in results if r.lifecycle == lifecycle]
    return [_to_dict(r) for r in results]


@router.get("/systems/{system_id}")
async def get_system(request: Request, system_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _store.get(_key(tenant_id, system_id))
    if not rec:
        raise HTTPException(status_code=404, detail="system not found")
    return _to_dict(rec)


@router.patch("/systems/{system_id}")
async def update_system(request: Request, system_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _key(tenant_id, system_id)
    rec = _store.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="system not found")
    updates: dict[str, Any] = {}
    if "name" in body:
        updates["name"] = str(body["name"])
    if "lifecycle" in body:
        updates["lifecycle"] = str(body["lifecycle"])
    if "approval" in body:
        updates["approval"] = str(body["approval"])
    if "policy_status" in body or "policyStatus" in body:
        updates["policy_status"] = str(body.get("policy_status") or body.get("policyStatus"))
    if "owner" in body:
        updates["owner"] = str(body["owner"])
    if "description" in body:
        updates["description"] = str(body["description"])
    if "metadata" in body and isinstance(body["metadata"], dict):
        updates["metadata"] = {**rec.metadata, **body["metadata"]}
    if not updates:
        return _to_dict(rec)
    from eaip.shared.time import utc_now
    updates["updated_at"] = utc_now()
    new = rec.model_copy(update=updates)
    _store[key] = new
    return _to_dict(new)


@router.post("/systems/{system_id}/risk", status_code=201)
async def assess_risk(request: Request, system_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _store.get(_key(tenant_id, system_id))
    if not rec:
        raise HTTPException(status_code=404, detail="system not found")
    raw = str(body.get("risk", "low"))
    try:
        new_risk = RiskLevel(raw.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid risk {raw!r}") from None
    prev = rec.risk
    assessment = RiskAssessment(assessment_id=f"ra-{uuid.uuid4().hex[:8]}", tenant_id=tenant_id, system_id=system_id, risk=new_risk, previous_risk=prev, rationale=str(body.get("rationale", "")), assessed_by=str(body.get("assessed_by") or _user.get("sub", "")), metadata=body.get("metadata") or {})
    _risk.setdefault(_key(tenant_id, system_id), []).append(assessment)
    from eaip.shared.time import utc_now
    updated = rec.model_copy(update={"risk": new_risk, "updated_at": utc_now()})
    _store[_key(tenant_id, system_id)] = updated
    return {"assessment_id": assessment.assessment_id, "system_id": system_id, "tenant_id": tenant_id, "risk": new_risk.value, "previous_risk": prev.value, "rationale": assessment.rationale, "created_at": assessment.created_at.isoformat()}


@router.get("/systems/{system_id}/risk")
async def list_risk(request: Request, system_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    if _key(tenant_id, system_id) not in _store:
        raise HTTPException(status_code=404, detail="system not found")
    assessments = _risk.get(_key(tenant_id, system_id), [])
    return [{"assessment_id": a.assessment_id, "system_id": a.system_id, "risk": a.risk.value, "previous_risk": a.previous_risk.value if a.previous_risk else None, "rationale": a.rationale, "created_at": a.created_at.isoformat()} for a in assessments]


@router.post("/policies", status_code=201)
async def create_policy(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    policy_id = str(body.get("policy_id") or body.get("policyId") or f"pol-{uuid.uuid4().hex[:8]}")
    key = _policy_key(tenant_id, policy_id)
    if key in _policies:
        raise HTTPException(status_code=409, detail="policy already exists")
    raw_thresh = str(body.get("risk_threshold") or body.get("riskThreshold") or "high")
    try:
        thresh = RiskLevel(raw_thresh.lower())
    except ValueError:
        thresh = RiskLevel.high
    rec = PolicyRecord(policy_id=policy_id, tenant_id=tenant_id, name=str(body.get("name") or policy_id), description=str(body.get("description", "")), allowed_actions=tuple(body.get("allowed_actions") or body.get("allowedActions") or []), risk_threshold=thresh, enabled=bool(body.get("enabled", True)), metadata=body.get("metadata") or {})
    _policies[key] = rec
    return _policy_to_dict(rec)


@router.get("/policies")
async def list_policies(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    prefix = f"{tenant_id}:"
    return [_policy_to_dict(v) for k, v in _policies.items() if k.startswith(prefix)]


@router.get("/policies/{policy_id}")
async def get_policy(request: Request, policy_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _policies.get(_policy_key(tenant_id, policy_id))
    if not rec:
        raise HTTPException(status_code=404, detail="policy not found")
    return _policy_to_dict(rec)


@router.post("/policies/{policy_id}/evaluate")
async def evaluate_policy(request: Request, policy_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _policies.get(_policy_key(tenant_id, policy_id))
    if not rec:
        raise HTTPException(status_code=404, detail="policy not found")
    action = str(body.get("action", ""))
    risk_str = str(body.get("risk", "low")).lower()
    try:
        req_risk = RiskLevel(risk_str)
    except ValueError:
        req_risk = RiskLevel.low
    risk_order = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
    allowed = True
    reason = "allowed"
    if not rec.enabled:
        allowed = False
        reason = "policy disabled"
    elif action and rec.allowed_actions and action not in rec.allowed_actions:
        allowed = False
        reason = f"action {action!r} not in allowed_actions"
    elif risk_order.get(req_risk.value, 0) > risk_order.get(rec.risk_threshold.value, 2):
        allowed = False
        reason = f"risk {req_risk.value} exceeds threshold {rec.risk_threshold.value}"
    return {"policy_id": policy_id, "tenant_id": tenant_id, "action": action, "risk": req_risk.value, "allowed": allowed, "reason": reason}


@router.get("/explain/{system_id}")
async def explain_system(request: Request, system_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _store.get(_key(tenant_id, system_id))
    if not rec:
        raise HTTPException(status_code=404, detail="system not found")
    assessments = _risk.get(_key(tenant_id, system_id), [])
    return {
        "system_id": system_id,
        "tenant_id": tenant_id,
        "what": {"name": rec.name, "type": rec.type.value, "lifecycle": rec.lifecycle, "approval": rec.approval},
        "why": {"risk": rec.risk.value, "policy_status": rec.policy_status, "risk_history": len(assessments)},
        "evidence": [{"assessment_id": a.assessment_id, "risk": a.risk.value, "rationale": a.rationale} for a in assessments[-5:]],
        "constraints": {"owner": rec.owner, "description": rec.description},
        "approval": rec.approval,
    }


__all__ = ["router"]
