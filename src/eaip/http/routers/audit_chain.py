from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/audit-chain", tags=["audit-chain"])


def _chain(req: Request):
    from eaip.audit_chain.chain import AuditChain
    chain = req.app.state.lifecycle.platform.container.try_resolve(AuditChain)
    if chain is None:
        chain = AuditChain()
        req.app.state.lifecycle.platform.container.register_instance(AuditChain, chain)
    return chain


@router.post("/append")
async def append_record(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    chain = _chain(request)
    actor = str(_user.get("sub") or _user.get("name") or "unknown")
    rec = chain.append(tenant_id=tenant_id, actor=actor, action=str(body.get("action", "unknown")), metadata=body.get("metadata"))
    return rec.model_dump(mode="json")


@router.get("")
async def list_records(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    chain = _chain(request)
    return [r.model_dump(mode="json") for r in chain.list_for_tenant(tenant_id)]


@router.post("/execution")
async def append_execution(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    chain = _chain(request)
    actor = str(_user.get("sub") or "unknown")
    import hashlib
    def _h(v: Any) -> str:
        if not v:
            return ""
        return hashlib.sha256(str(v).encode()).hexdigest()[:16]
    rec = chain.append_execution(tenant_id=tenant_id, actor=actor, execution_id=str(body.get("execution_id") or body.get("executionId") or "exec-1"), inputs_hash=_h(body.get("inputs")), policy_hash=_h(body.get("policy")), tool_hash=_h(body.get("tool")), output_hash=_h(body.get("output")))
    return rec.model_dump(mode="json")


@router.get("/verify/{record_id}")
async def verify_execution(request: Request, record_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    chain = _chain(request)
    return chain.verify_execution(tenant_id, record_id)


@router.get("/verify")
async def verify_chain(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    chain = _chain(request)
    return chain.verify(tenant_id)
