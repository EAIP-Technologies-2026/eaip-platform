from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/federation", tags=["federation"])


def _svc(req: Request):
    from eaip.federation.service import FederationService
    svc = req.app.state.lifecycle.platform.container.try_resolve(FederationService)
    if svc is None:
        svc = FederationService()
        req.app.state.lifecycle.platform.container.register_instance(FederationService, svc)
    return svc


@router.post("/orgs")
async def create_org(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    org_id = str(body.get("org_id") or body.get("orgId") or f"org-{tenant_id[:4]}-{len(svc.list_for_tenant(tenant_id))+1}")
    try:
        org = svc.create_org(org_id=org_id, tenant_id=tenant_id, name=str(body.get("name", org_id)), parent_org_id=str(body.get("parent_org_id") or body.get("parentOrgId") or ""), metadata=body.get("metadata"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return org.model_dump(mode="json")


@router.get("/orgs")
async def list_orgs(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    svc = _svc(request)
    return [o.model_dump(mode="json") for o in svc.list_for_tenant(tenant_id)]


@router.get("/orgs/{org_id}")
async def get_org(request: Request, org_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    org = svc.get(org_id)
    if not org or org.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="org not found")
    return org.model_dump(mode="json")


@router.get("/orgs/{org_id}/children")
async def list_children(request: Request, org_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    svc = _svc(request)
    org = svc.get(org_id)
    if not org or org.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="org not found")
    return [o.model_dump(mode="json") for o in svc.children_of(org_id)]


@router.post("/trusts")
async def create_trust(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    return svc.create_trust(from_org=str(body.get("from_org", "")), to_org=str(body.get("to_org", "")), tenant_id=tenant_id, scopes=body.get("scopes"))


@router.get("/trusts")
async def list_trusts(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _svc(request).list_trusts(tenant_id)


@router.post("/delegations")
async def create_delegation(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _svc(request).create_delegation(who=str(body.get("who", "")), what=str(body.get("what", "")), purpose=str(body.get("purpose", "")), tenant_id=tenant_id, ttl_seconds=int(body.get("ttl_seconds", 3600)))


@router.get("/delegations")
async def list_delegations(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _svc(request).list_delegations(tenant_id)


@router.get("/delegations/{delegation_id}")
async def check_delegation(request: Request, delegation_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _svc(request).check_delegation(delegation_id)


@router.post("/check-access")
async def check_access(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _svc(request).check_access(str(body.get("requester_org", "")), str(body.get("target_org", "")), tenant_id=tenant_id)


@router.get("/audit")
async def federation_audit(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _svc(request).audit_log(tenant_id)


@router.post("/cross-workflow")
async def cross_workflow(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.audit_chain.chain import AuditChain
    chain = request.app.state.lifecycle.platform.container.try_resolve(AuditChain)
    actor = str(_user.get("sub") or "unknown")
    steps = ["crm_read", "agent_process", "project_write", "audit"]
    if chain:
        for step in steps:
            chain.append(tenant_id=tenant_id, actor=actor, action=f"cross:{step}", metadata={"flow": body.get("flow", "crm→agent→project")})
    return {"tenant_id": tenant_id, "flow": body.get("flow", "crm→agent→project"), "steps": steps, "status": "completed", "audit": True}
