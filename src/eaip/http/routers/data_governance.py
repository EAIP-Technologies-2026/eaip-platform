from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/data-governance", tags=["data-governance"])


@router.get("/classification")
async def classification_info(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {"tenant_id": tenant_id, "levels": ["public", "internal", "confidential", "restricted"], "default": "internal"}


@router.get("/retention")
async def retention_policies(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {"tenant_id": tenant_id, "policies": [{"resource": "audit", "retention_days": 365}, {"resource": "documents", "retention_days": 730}, {"resource": "events", "retention_days": 90}, {"resource": "telemetry", "retention_days": 30}], "note": "No automatic deletion without explicit policy"}


@router.get("/lineage/{resource_id}")
async def lineage(request: Request, resource_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {"resource_id": resource_id, "tenant_id": tenant_id, "lineage": ["source", "transformation", "knowledge", "decision", "action"], "provenance": f"tenant:{tenant_id}"}
