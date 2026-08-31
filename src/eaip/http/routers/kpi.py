from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/kpi", tags=["kpi"])

_kpis: list[dict[str, Any]] = []


@router.post("", status_code=201)
async def create_kpi(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"kpi_id": body.get("kpi_id") or f"kpi-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "goal": str(body.get("goal", "")), "name": str(body.get("name", "KPI")), "target": float(body.get("target", 100)), "actual": float(body.get("actual", 0)), "trend": str(body.get("trend", "flat")), "confidence": float(body.get("confidence", 0.5)), "owner": str(body.get("owner", "")), "source": str(body.get("source", "manual"))}
    _kpis.append(rec)
    return rec


@router.get("")
async def list_kpis(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [k for k in _kpis if k["tenant_id"] == tenant_id]


@router.patch("/{kpi_id}")
async def update_kpi(request: Request, kpi_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    for k in _kpis:
        if k["kpi_id"] == kpi_id and k["tenant_id"] == tenant_id:
            for field in ("actual", "target", "trend", "confidence"):
                if field in body:
                    k[field] = body[field]
            return k
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="kpi not found")


@router.get("/outcome")
async def outcome_summary(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    tenant_kpis = [k for k in _kpis if k["tenant_id"] == tenant_id]
    if not tenant_kpis:
        return {"tenant_id": tenant_id, "kpis": [], "summary": "no kpis"}
    avg_progress = sum((k["actual"] / max(k["target"], 1) * 100) for k in tenant_kpis) / len(tenant_kpis)
    return {"tenant_id": tenant_id, "kpis": tenant_kpis, "avg_progress_pct": round(avg_progress, 1), "count": len(tenant_kpis)}
