from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.workforce.analytics import WorkforceAnalyticsService

router = APIRouter(prefix="/workforce/analytics", tags=["workforce-analytics"])


def _get_analytics(request: Request) -> WorkforceAnalyticsService:
    svc = request.app.state.lifecycle.platform.container.try_resolve(WorkforceAnalyticsService)
    if svc is not None:
        return svc
    registry = request.app.state.lifecycle.platform.container.try_resolve("WorkerRegistry")
    orchestrator = request.app.state.lifecycle.platform.container.try_resolve("WorkforceOrchestrator")
    return WorkforceAnalyticsService(registry=registry, orchestrator=orchestrator)


@router.get("/overview")
async def overview(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None or svc._orchestrator is None:
        return {"tenant_id": tenant_id, "total_workers": 0, "utilization": 0.0}
    return {"tenant_id": tenant_id, **svc.get_overview(tenant_id)}


@router.get("/utilization")
async def utilization(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    days: int = 7,
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None:
        return {"tenant_id": tenant_id, "series": []}
    series = svc.get_utilization_timeseries(tenant_id, days=min(days, 30))
    return {"tenant_id": tenant_id, "series": series}


@router.get("/workload")
async def workload(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None:
        return {"tenant_id": tenant_id, "distribution": []}
    dist = svc.get_workload_distribution(tenant_id)
    return {"tenant_id": tenant_id, "distribution": dist}


@router.get("/capacity")
async def capacity(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None:
        return {"tenant_id": tenant_id, "total_capacity": 0}
    return {"tenant_id": tenant_id, **svc.get_capacity(tenant_id)}


@router.get("/bottlenecks")
async def bottlenecks(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None:
        return {"tenant_id": tenant_id, "bottlenecks": []}
    items = svc.detect_bottlenecks(tenant_id)
    return {"tenant_id": tenant_id, "bottlenecks": items}


@router.get("/recommendations")
async def recommendations(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None:
        return {"tenant_id": tenant_id, "recommendations": []}
    items = svc.get_recommendations(tenant_id)
    return {"tenant_id": tenant_id, "recommendations": items}


@router.get("/trends")
async def trends(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    days: int = 30,
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None:
        return {"tenant_id": tenant_id, "utilization": {}, "throughput": {}}
    return {"tenant_id": tenant_id, **svc.get_trends(tenant_id, days=min(days, 90))}


@router.get("/workers/{worker_id}/performance")
async def worker_performance(
    request: Request,
    worker_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_analytics(request)
    if svc._registry is None:
        raise HTTPException(status_code=503, detail="workforce not available")
    result = svc.get_worker_performance(worker_id, tenant_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
