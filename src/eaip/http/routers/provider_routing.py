from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/provider-routing", tags=["provider-routing"])

# In-memory provider registry — extends existing provider_routing
_providers: list[dict[str, Any]] = []


@router.get("/providers")
async def list_providers(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [p for p in _providers if p.get("tenant_id") in (tenant_id, "global")]


@router.post("/providers", status_code=201)
async def register_provider(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"provider_id": body.get("provider_id") or body.get("name") or "provider-1", "tenant_id": tenant_id, "model": str(body.get("model", "gpt-4")), "version": str(body.get("version", "1.0")), "capability": str(body.get("capability", "chat")), "cost": float(body.get("cost", 0.01)), "latency_ms": float(body.get("latency_ms", 200)), "availability": float(body.get("availability", 0.99)), "risk": str(body.get("risk", "low")), "evaluation_score": float(body.get("evaluation_score", 0.8))}
    _providers.append(rec)
    return rec


@router.post("/route")
async def route_provider(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    cap = str(body.get("capability", "chat"))
    max_cost = body.get("max_cost")
    max_latency = body.get("max_latency")
    candidates = [p for p in _providers if p.get("tenant_id") in (tenant_id, "global") and (not cap or p.get("capability") == cap)]
    if max_cost is not None:
        candidates = [p for p in candidates if p["cost"] <= float(max_cost)]
    if max_latency is not None:
        candidates = [p for p in candidates if p["latency_ms"] <= float(max_latency)]
    if not candidates:
        return {"tenant_id": tenant_id, "selected": None, "reason": "no candidate"}
    candidates.sort(key=lambda x: (-x["evaluation_score"], x["cost"]))
    return {"tenant_id": tenant_id, "selected": candidates[0], "candidates": len(candidates)}


@router.post("/failover")
async def failover(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    failed = str(body.get("failed_provider", ""))
    cap = str(body.get("capability", "chat"))
    candidates = [p for p in _providers if p.get("provider_id") != failed and p.get("tenant_id") in (tenant_id, "global") and (not cap or p.get("capability") == cap)]
    if not candidates:
        return {"tenant_id": tenant_id, "failover": None, "reason": "no fallback"}
    candidates.sort(key=lambda x: (-x["evaluation_score"], x["cost"]))
    return {"tenant_id": tenant_id, "failed": failed, "failover": candidates[0]}
