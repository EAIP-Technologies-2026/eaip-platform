from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])

_flags: dict[str, dict[str, Any]] = {}


@router.get("")
async def list_flags(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [v for v in _flags.values() if v.get("tenant_id") in (tenant_id, "global", "*")]


@router.put("/{flag_id}")
async def put_flag(request: Request, flag_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"flag_id": flag_id, "tenant_id": tenant_id, "enabled": bool(body.get("enabled", False)), "rollout_pct": int(body.get("rollout_pct", body.get("rollout", 0))), "tenants": body.get("tenants") or [], "version": str(body.get("version", "1.0")), "environment": str(body.get("environment", "production"))}
    _flags[f"{tenant_id}:{flag_id}"] = rec
    return rec


@router.get("/{flag_id}/check")
async def check_flag(request: Request, flag_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _flags.get(f"{tenant_id}:{flag_id}") or _flags.get(f"global:{flag_id}")
    if not rec:
        return {"flag_id": flag_id, "enabled": False, "reason": "not found"}
    if rec.get("tenants") and tenant_id not in rec["tenants"]:
        return {"flag_id": flag_id, "enabled": False, "reason": "tenant not in rollout"}
    return {"flag_id": flag_id, "enabled": rec["enabled"], "rollout_pct": rec["rollout_pct"]}
