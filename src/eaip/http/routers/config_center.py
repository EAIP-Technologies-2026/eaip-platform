from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/config-center", tags=["config-center"])

_config: dict[str, dict[str, Any]] = {}


@router.get("")
async def get_config(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    cfg = _config.get(tenant_id, {"tenant_id": tenant_id, "organization": {}, "users": [], "roles": [], "autonomy": {}, "policies": [], "budgets": [], "runtimes": [], "connectors": [], "retention": {}, "notifications": {}})
    return cfg


@router.put("")
async def put_config(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    existing = _config.get(tenant_id, {})
    merged = {**existing, **body, "tenant_id": tenant_id}
    _config[tenant_id] = merged
    return merged


@router.patch("")
async def patch_config(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    existing = _config.get(tenant_id, {"tenant_id": tenant_id})
    for k, v in body.items():
        existing[k] = v
    _config[tenant_id] = existing
    return existing
