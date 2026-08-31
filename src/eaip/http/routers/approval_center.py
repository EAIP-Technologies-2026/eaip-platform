from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/approval-center", tags=["approval-center"])

_approvals: list[dict[str, Any]] = []


def get_pending_for_tenant(tenant_id: str) -> list[dict[str, Any]]:
    """Return all pending approval-center items scoped to a tenant.

    Used by the unified approval inbox aggregation (do not duplicate state).
    """
    return [a for a in _approvals if a["tenant_id"] == tenant_id and a["status"] == "pending"]


@router.get("")
async def list_approvals(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), status: str = "") -> list[dict[str, Any]]:
    items = [a for a in _approvals if a["tenant_id"] == tenant_id]
    if status:
        items = [a for a in items if a["status"] == status]
    return items


@router.post("", status_code=201)
async def create_approval(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"approval_id": body.get("approval_id") or f"appr-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "type": str(body.get("type", "general")), "title": str(body.get("title", "Approval required")), "status": "pending", "requester": str(_user.get("sub", "system") if isinstance(_user, dict) else "system"), "metadata": body.get("metadata") or {}}
    _approvals.append(rec)
    return rec


@router.post("/{approval_id}/approve")
async def approve(request: Request, approval_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    for a in _approvals:
        if a["approval_id"] == approval_id and a["tenant_id"] == tenant_id:
            a["status"] = "approved"
            a["decided_by"] = str(_user.get("sub", "system") if isinstance(_user, dict) else "system")
            return a
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="approval not found")


@router.post("/{approval_id}/reject")
async def reject(request: Request, approval_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    for a in _approvals:
        if a["approval_id"] == approval_id and a["tenant_id"] == tenant_id:
            a["status"] = "rejected"
            a["decided_by"] = str(_user.get("sub", "system") if isinstance(_user, dict) else "system")
            return a
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="approval not found")


@router.post("/{approval_id}/defer")
async def defer(request: Request, approval_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    for a in _approvals:
        if a["approval_id"] == approval_id and a["tenant_id"] == tenant_id:
            a["status"] = "deferred"
            return a
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="approval not found")
