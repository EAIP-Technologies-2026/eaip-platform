from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/long-missions", tags=["long-missions"])


def _svc(req: Request):
    from eaip.long_missions.service import LongMissionService
    svc = req.app.state.lifecycle.platform.container.try_resolve(LongMissionService)
    if svc is None:
        svc = LongMissionService()
        req.app.state.lifecycle.platform.container.register_instance(LongMissionService, svc)
    return svc


@router.post("")
async def create_mission(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    mission_id = str(body.get("mission_id") or body.get("missionId") or f"lm-{uuid.uuid4().hex[:8]}")
    rec = svc.create(mission_id=mission_id, tenant_id=tenant_id, name=str(body.get("name", mission_id)), steps=body.get("steps"), autonomy_level=str(body.get("autonomy_level") or body.get("autonomyLevel") or "SUGGEST"), metadata=body.get("metadata"))
    return rec.model_dump(mode="json")


@router.get("")
async def list_missions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    svc = _svc(request)
    return [r.model_dump(mode="json") for r in svc.list_for_tenant(tenant_id)]


@router.get("/{mission_id}")
async def get_mission(request: Request, mission_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    rec = svc.get(mission_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="mission not found")
    return rec.model_dump(mode="json")


@router.post("/{mission_id}/checkpoint")
async def checkpoint_mission(request: Request, mission_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    cp = svc.checkpoint(mission_id, tenant_id, state=body or {})
    if not cp:
        raise HTTPException(status_code=404, detail="mission not found")
    return cp.model_dump(mode="json")


@router.post("/{mission_id}/pause")
async def pause_mission(request: Request, mission_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    rec = svc.pause(mission_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="mission not found")
    return rec.model_dump(mode="json")


@router.post("/{mission_id}/resume")
async def resume_mission(request: Request, mission_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    rec = svc.resume(mission_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="mission not found")
    return rec.model_dump(mode="json")


@router.post("/{mission_id}/cancel")
async def cancel_mission(request: Request, mission_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    rec = svc.cancel(mission_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="mission not found")
    return rec.model_dump(mode="json")


@router.post("/{mission_id}/advance")
async def advance_mission(request: Request, mission_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    rec = svc.advance(mission_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="mission not found")
    return rec.model_dump(mode="json")


@router.post("/{mission_id}/recover")
async def recover_mission(request: Request, mission_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    rec = svc.recover(mission_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="mission not found")
    return rec.model_dump(mode="json")


@router.post("/{mission_id}/escalate")
async def escalate_mission(request: Request, mission_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    reason = str((body or {}).get("reason", ""))
    rec = svc.escalate(mission_id, tenant_id, reason=reason)
    if not rec:
        raise HTTPException(status_code=404, detail="mission not found")
    return rec.model_dump(mode="json")


@router.post("/{mission_id}/propose-workflow")
async def propose_workflow(request: Request, mission_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    try:
        return svc.propose_workflow(mission_id, tenant_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
