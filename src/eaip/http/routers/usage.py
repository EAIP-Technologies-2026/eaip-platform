from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/usage", tags=["usage"])

_usage: dict[str, dict[str, Any]] = {}


def _get(tenant_id: str) -> dict[str, Any]:
    if tenant_id not in _usage:
        _usage[tenant_id] = {"tenant_id": tenant_id, "active_users": 0, "agents": 0, "executions": 0, "tokens": 0, "connector_calls": 0, "simulations": 0, "storage_mb": 0, "documents": 0, "runtime_seconds": 0}
    return _usage[tenant_id]


@router.get("")
async def get_usage(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _get(tenant_id)


@router.post("/record", status_code=201)
async def record_usage(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _get(tenant_id)
    for k in ("active_users", "agents", "executions", "tokens", "connector_calls", "simulations", "storage_mb", "documents", "runtime_seconds"):
        if k in body:
            rec[k] = int(rec[k]) + int(body[k])
    return rec


@router.get("/dashboard")
async def usage_dashboard(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    u = _get(tenant_id)
    return {"tenant_id": tenant_id, "usage": u, "note": "metering only — no payment processing"}
