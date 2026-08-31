from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def _svc(req: Request):
    from eaip.onboarding.service import OnboardingService
    svc = req.app.state.lifecycle.platform.container.try_resolve(OnboardingService)
    if svc is None:
        svc = OnboardingService()
        req.app.state.lifecycle.platform.container.register_instance(OnboardingService, svc)
    return svc


@router.post("/sessions")
async def create_session(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    company_name = str(body.get("company_name") or body.get("companyName") or "").strip()
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name required")
    svc = _svc(request)
    sess = svc.create(tenant_id=tenant_id, company_name=company_name, industry=str(body.get("industry", "")), pack_id=str(body.get("pack_id") or body.get("packId") or ""), metadata=body.get("metadata"))
    return sess.model_dump(mode="json")


@router.get("/sessions")
async def list_sessions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    svc = _svc(request)
    return [s.model_dump(mode="json") for s in svc.list_for_tenant(tenant_id)]


@router.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    sess = svc.get(session_id, tenant_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    return sess.model_dump(mode="json")


@router.post("/sessions/{session_id}/advance")
async def advance_session(request: Request, session_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    sess = await svc.advance(session_id, tenant_id, step_data=body or {})
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    return sess.model_dump(mode="json")


@router.patch("/sessions/{session_id}")
async def patch_session(request: Request, session_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    sess = svc.update(session_id, tenant_id, body)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    return sess.model_dump(mode="json")
