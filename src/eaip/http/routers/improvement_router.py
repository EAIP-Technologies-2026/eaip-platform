from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.improvement.service import ImprovementService
from eaip.logging.context import get_logger

router = APIRouter(prefix="/improvements", tags=["improvements"])
log = get_logger("eaip.http.routers.improvements")


def _service(request: Request) -> ImprovementService:
    svc = request.app.state.lifecycle.platform.container.try_resolve(ImprovementService)
    if svc is None:
        svc = ImprovementService()
        try:
            request.app.state.lifecycle.platform.container.register_instance(ImprovementService, svc)
        except Exception:
            pass
    return svc


def _to_dict(p: Any) -> dict[str, Any]:
    return {
        "proposal_id": p.proposal_id,
        "proposalId": p.proposal_id,
        "tenant_id": p.tenant_id,
        "tenantId": p.tenant_id,
        "source": p.source,
        "problem": dict(p.problem),
        "root_cause": p.root_cause,
        "rootCause": p.root_cause,
        "proposed_change": p.proposed_change,
        "proposedChange": p.proposed_change,
        "expected_benefit": p.expected_benefit,
        "expectedBenefit": p.expected_benefit,
        "risk": p.risk,
        "evidence": list(p.evidence),
        "simulation": dict(p.simulation),
        "approval": dict(p.approval),
        "implementation": dict(p.implementation),
        "measured_outcome": dict(p.measured_outcome),
        "measuredOutcome": dict(p.measured_outcome),
        "status": p.status,
        "created_at": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at),
        "createdAt": p.created_at.isoformat() if hasattr(p.created_at, "isoformat") else str(p.created_at),
        "updated_at": p.updated_at.isoformat() if hasattr(p.updated_at, "isoformat") else str(p.updated_at),
        "updatedAt": p.updated_at.isoformat() if hasattr(p.updated_at, "isoformat") else str(p.updated_at),
    }


@router.post("", status_code=201)
@router.post("/", status_code=201, include_in_schema=False)
async def propose(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    problem = body.get("problem") or {k: v for k, v in body.items() if k not in {"source", "root_cause", "rootCause", "proposed_change", "proposedChange", "expected_benefit", "expectedBenefit", "evidence"}}
    if not isinstance(problem, dict):
        raise HTTPException(status_code=400, detail="problem must be an object")
    source = str(body.get("source", "manual"))
    root_cause = str(body.get("root_cause") or body.get("rootCause") or "")
    proposed_change = str(body.get("proposed_change") or body.get("proposedChange") or "")
    expected_benefit = str(body.get("expected_benefit") or body.get("expectedBenefit") or "")
    evidence = body.get("evidence")
    if evidence is not None and not isinstance(evidence, list):
        raise HTTPException(status_code=400, detail="evidence must be a list")
    prop = svc.propose(tenant=tenant_id, source=source, problem=problem, root_cause=root_cause, proposed_change=proposed_change, expected_benefit=expected_benefit, evidence=evidence)
    log.info("improvement.proposed", proposal_id=prop.proposal_id, tenant_id=tenant_id)
    return _to_dict(prop)


@router.get("", include_in_schema=False)
@router.get("/")
async def list_proposals(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), status: str | None = None, source: str | None = None) -> list[dict[str, Any]]:
    svc = _service(request)
    proposals = svc.list_for_tenant(tenant_id)
    if status:
        proposals = [p for p in proposals if p.status == status]
    if source:
        proposals = [p for p in proposals if p.source == source]
    return [_to_dict(p) for p in proposals]


@router.get("/{proposal_id}")
async def get_proposal(request: Request, proposal_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    prop = svc.get(proposal_id, tenant_id)
    if not prop:
        raise HTTPException(status_code=404, detail="proposal not found")
    return _to_dict(prop)


@router.post("/{proposal_id}/review")
async def review_proposal(request: Request, proposal_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    approved = body.get("approved")
    if approved is None:
        approved = body.get("approve")
    if approved is None:
        raise HTTPException(status_code=400, detail="approved boolean required")
    approved_bool = bool(approved) if isinstance(approved, bool) else str(approved).lower() in ("true", "1", "yes", "approved")
    result = svc.review(proposal_id, tenant_id, approved_bool)
    if not result:
        raise HTTPException(status_code=404, detail="proposal not found")
    return _to_dict(result)


@router.post("/{proposal_id}/apply")
async def apply_proposal(request: Request, proposal_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    try:
        result = svc.apply(proposal_id, tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="proposal not found")
    return _to_dict(result)


@router.post("/{proposal_id}/measure")
async def measure_proposal(request: Request, proposal_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _service(request)
    outcome = body.get("outcome") or body.get("measured_outcome") or body.get("measuredOutcome") or body
    if outcome is body:
        outcome = {k: v for k, v in body.items() if k not in {"proposal_id", "tenant_id"}}
    if not isinstance(outcome, dict):
        outcome = {"outcome": str(outcome)}
    try:
        result = svc.measure(proposal_id, tenant_id, outcome)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="proposal not found")
    return _to_dict(result)


__all__ = ["router"]
