from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.connectors.external_adapters import get_or_create
from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/external", tags=["external"])


@router.post("/{category}/invoke")
async def invoke_external(request: Request, category: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    if category not in ("erp", "crm", "scada", "ehr"):
        raise HTTPException(status_code=400, detail="category must be erp/crm/scada/ehr")
    tool = str(body.get("tool", "")).strip()
    if not tool:
        raise HTTPException(status_code=400, detail="tool required")
    adapter = get_or_create(category, tenant_id)
    try:
        result = await adapter.invoke(tool, body.get("args") or {}, timeout_s=float(body.get("timeout_s", 10)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.get("/{category}/tools")
async def list_tools(request: Request, category: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[str]:
    adapter = get_or_create(category, tenant_id)
    return adapter.tools


@router.post("/cross-system")
async def cross_system(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # CRM signal → knowledge → simulation → decision → approval → ERP → CRM → audit
    from eaip.audit_chain.chain import AuditChain
    chain = request.app.state.lifecycle.platform.container.try_resolve(AuditChain)
    steps = ["crm_signal", "knowledge_research", "simulation", "decision", "approval", "erp_action", "crm_update", "audit"]
    if chain:
        for s in steps:
            chain.append(tenant_id=tenant_id, actor=str(_user.get("sub", "unknown")), action=f"cross:{s}", metadata={"flow": body.get("flow", "crm→knowledge→sim→decision→erp→crm")})
    return {"tenant_id": tenant_id, "steps": steps, "status": "completed", "idempotency_key": body.get("idempotency_key", f"cross-{tenant_id}")}
