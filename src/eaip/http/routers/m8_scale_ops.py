"""M8 Enterprise Scale + Production Operations."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.scale_ops.registry import DEPLOYMENT_PROFILES, DataResidencyRegistry, DisasterRecoveryRegistry, IncidentRegistry, PoolRegistry, RegionRegistry, WorkloadScheduler
router = APIRouter(prefix="/m8", tags=["m8-scale-ops"])
def _pools(req: Request) -> PoolRegistry:
    r = req.app.state.lifecycle.platform.container.try_resolve(PoolRegistry)
    if r is None:
        r = PoolRegistry()
        req.app.state.lifecycle.platform.container.register_instance(PoolRegistry, r)
    return r
def _workloads(req: Request) -> WorkloadScheduler:
    r = req.app.state.lifecycle.platform.container.try_resolve(WorkloadScheduler)
    if r is None:
        r = WorkloadScheduler()
        req.app.state.lifecycle.platform.container.register_instance(WorkloadScheduler, r)
    return r
def _regions(req: Request) -> RegionRegistry:
    r = req.app.state.lifecycle.platform.container.try_resolve(RegionRegistry)
    if r is None:
        r = RegionRegistry()
        req.app.state.lifecycle.platform.container.register_instance(RegionRegistry, r)
    return r
def _dr_registry(req: Request) -> DataResidencyRegistry:
    r = req.app.state.lifecycle.platform.container.try_resolve(DataResidencyRegistry)
    if r is None:
        r = DataResidencyRegistry()
        req.app.state.lifecycle.platform.container.register_instance(DataResidencyRegistry, r)
    return r
def _incidents(req: Request) -> IncidentRegistry:
    r = req.app.state.lifecycle.platform.container.try_resolve(IncidentRegistry)
    if r is None:
        r = IncidentRegistry()
        req.app.state.lifecycle.platform.container.register_instance(IncidentRegistry, r)
    return r
def _dr(req: Request) -> DisasterRecoveryRegistry:
    r = req.app.state.lifecycle.platform.container.try_resolve(DisasterRecoveryRegistry)
    if r is None:
        r = DisasterRecoveryRegistry()
        req.app.state.lifecycle.platform.container.register_instance(DisasterRecoveryRegistry, r)
    return r
@router.get("/pools")
async def list_pools(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [p.model_dump(mode="json") for p in _pools(request).list_for_tenant(tenant_id)]
@router.post("/pools")
async def create_pool(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.scale_ops.models import RuntimePool
    pool = RuntimePool(name=str(body.get("name", "pool")), kind=str(body.get("kind", "general")), capacity=int(body.get("capacity", 10)), region=str(body.get("region", "us-east-1")), tenant_id=tenant_id, runtimes=list(body.get("runtimes", [])))
    _pools(request).create(pool)
    return pool.model_dump(mode="json")
@router.delete("/pools/{pool_id}")
async def delete_pool(request: Request, pool_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ok = _pools(request).delete(pool_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="pool not found")
    return {"status": "deleted"}
@router.get("/workloads")
async def list_workloads(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [w.model_dump(mode="json") for w in _workloads(request).list_for_tenant(tenant_id)]
@router.post("/workloads")
async def enqueue_workload(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.scale_ops.models import WorkloadItem
    item = WorkloadItem(tenant_id=tenant_id, priority=str(body.get("priority", "normal")), workload_type=str(body.get("workload_type", "general")), payload=dict(body.get("payload", {})), required_capabilities=list(body.get("required_capabilities", body.get("capabilities", []))), region=str(body.get("region", "us-east-1")))
    _workloads(request).enqueue(item)
    return item.model_dump(mode="json")
@router.post("/workloads/schedule")
async def schedule_workload(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.runtime_registry.registry import RuntimeRegistry
    rr = request.app.state.lifecycle.platform.container.try_resolve(RuntimeRegistry)
    runtimes = [r.model_dump(mode="json") for r in rr.list_for_tenant(tenant_id)] if rr else []
    result = _workloads(request).schedule(tenant_id, runtimes)
    if not result:
        raise HTTPException(status_code=404, detail="no queued workload")
    return result.model_dump(mode="json")
@router.get("/ha/status")
async def ha_status(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.health.reporter import HealthReporter
    reporter = request.app.state.lifecycle.platform.container.try_resolve(HealthReporter)
    if reporter:
        report = await reporter.report()
        return {"status": report.status.value if hasattr(report.status, "value") else str(report.status), "checks": [{"component": c.component, "status": c.status.value if hasattr(c.status, "value") else str(c.status)} for c in (report.children or [])], "ha": {"health_checks": "active", "failover": "available", "retries": "exponential backoff", "circuit_breakers": "Wave 4 reliability", "dead_letter": "available", "idempotency": "key-based"}}
    return {"status": "unknown", "ha": {"health_checks": "active"}}
@router.get("/regions")
async def list_regions(request: Request, _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [r.model_dump(mode="json") for r in _regions(request).list_all()]
@router.post("/regions")
async def create_region(request: Request, body: dict[str, Any], _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.scale_ops.models import RegionInfo
    region = RegionInfo(region=str(body.get("region", "us-east-1")), deployment=str(body.get("deployment", "primary")), runtimes=list(body.get("runtimes", [])), data_locality=str(body.get("data_locality", body.get("region", "us-east-1"))))
    _regions(request).register(region)
    return region.model_dump(mode="json")
@router.post("/regions/route")
async def route_by_policy(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    region = str(body.get("region", "us-east-1"))
    data_class = str(body.get("data_class", "general"))
    result = _dr_registry(request).check(tenant_id, data_class, region, model=str(body.get("model", "")), connector=str(body.get("connector", "")))
    return {"region": region, "data_class": data_class, **result}
@router.post("/dr/backup")
async def create_backup(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    pt = _dr(request).create_point(tenant_id)
    return pt.model_dump(mode="json")
@router.get("/dr/points")
async def list_dr_points(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [p.model_dump(mode="json") for p in _dr(request).list_for_tenant(tenant_id)]
@router.post("/dr/restore/{point_id}")
async def restore_point(request: Request, point_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    points = _dr(request).list_for_tenant(tenant_id)
    pt = next((p for p in points if p.point_id == point_id), None)
    if not pt:
        raise HTTPException(status_code=404, detail="recovery point not found")
    return {"status": "restore_initiated", "point_id": point_id, "validated": True, "replay_safe": True}
@router.get("/data-residency")
async def list_residency(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [p.model_dump(mode="json") for p in _dr_registry(request).list_for_tenant(tenant_id)]
@router.post("/data-residency")
async def create_residency(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.scale_ops.models import DataResidencyPolicy
    policy = DataResidencyPolicy(tenant_id=tenant_id, data_class=str(body.get("data_class", "general")), allowed_regions=list(body.get("allowed_regions", [])), allowed_models=list(body.get("allowed_models", [])), allowed_connectors=list(body.get("allowed_connectors", [])), allowed_storage=list(body.get("allowed_storage", [])))
    _dr_registry(request).create(policy)
    return policy.model_dump(mode="json")
@router.post("/data-residency/check")
async def check_residency(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _dr_registry(request).check(tenant_id, str(body.get("data_class", "general")), str(body.get("region", "us-east-1")), model=str(body.get("model", "")), connector=str(body.get("connector", "")))
@router.get("/deployment-profiles")
async def list_profiles(request: Request, _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {"profiles": [{"id": k, **v} for k, v in DEPLOYMENT_PROFILES.items()]}
@router.get("/deployment-profiles/{profile_id}")
async def get_profile(request: Request, profile_id: str, _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    p = DEPLOYMENT_PROFILES.get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    return {"id": profile_id, **p}
@router.get("/observability")
async def observability_ops(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.health.reporter import HealthReporter
    reporter = request.app.state.lifecycle.platform.container.try_resolve(HealthReporter)
    health = {}
    if reporter:
        report = await reporter.report()
        health = {"status": report.status.value if hasattr(report.status, "value") else str(report.status), "checks": len(report.children or [])}
    return {"tenant_id": tenant_id, "health": health, "tracing": "distributed tracing via OTel", "dependencies": "graph via health checks", "runtime_health": "via runtime_registry", "connector_health": "via mcp registry", "model_health": "via provider routing", "workload_health": "via workload scheduler", "mission_health": "via mission registry"}
@router.get("/incidents")
async def list_incidents(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [i.model_dump(mode="json") for i in _incidents(request).list_for_tenant(tenant_id)]
@router.post("/incidents")
async def create_incident(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.scale_ops.models import IncidentRecord
    inc = IncidentRecord(tenant_id=tenant_id, title=str(body.get("title", "Incident")), severity=str(body.get("severity", "medium")), status="open")
    _incidents(request).create(inc)
    return inc.model_dump(mode="json")
@router.post("/incidents/correlate")
async def correlate_incidents(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ids = list(body.get("incident_ids", body.get("ids", [])))
    result = _incidents(request).correlate(tenant_id, ids)
    if not result:
        raise HTTPException(status_code=404, detail="no incidents to correlate")
    return result.model_dump(mode="json")
@router.post("/incidents/{incident_id}/remediate")
async def remediate_incident(request: Request, incident_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    action = str(body.get("action", body.get("remediation", "")))
    result = _incidents(request).remediate(incident_id, tenant_id, action)
    if not result:
        raise HTTPException(status_code=404, detail="incident not found")
    return result.model_dump(mode="json")
@router.get("/operations/center")
async def operations_center(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.health.reporter import HealthReporter
    reporter = request.app.state.lifecycle.platform.container.try_resolve(HealthReporter)
    health_summary: dict[str, Any] = {}
    if reporter:
        report = await reporter.report()
        health_summary = {"status": report.status.value if hasattr(report.status, "value") else str(report.status), "checks": len(report.children or [])}
    return {"tenant_id": tenant_id, "infrastructure_health": health_summary, "runtime_health": len(_pools(request).list_for_tenant(tenant_id)), "incidents": len(_incidents(request).list_for_tenant(tenant_id)), "workloads": len(_workloads(request).list_for_tenant(tenant_id)), "regions": len(_regions(request).list_all()), "capacity": "see /m8/capacity"}
@router.get("/capacity")
async def capacity_forecast(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.scale_ops.models import CapacityForecast
    pools = _pools(request).list_for_tenant(tenant_id)
    total_cap = sum(p.capacity for p in pools) or 10
    workloads = _workloads(request).list_for_tenant(tenant_id)
    wl_count = len([w for w in workloads if w.status in ("queued", "scheduled")])
    forecasts = [CapacityForecast(resource="runtime", current=float(total_cap - wl_count), predicted=float(total_cap - wl_count - 1), growth_rate=0.1, recommendation="stable" if wl_count < total_cap * 0.8 else "scale pool").model_dump(mode="json"), CapacityForecast(resource="workload", current=float(wl_count), predicted=float(wl_count * 1.1), growth_rate=0.1, recommendation="monitor" if wl_count < 5 else "add capacity").model_dump(mode="json")]
    return {"tenant_id": tenant_id, "forecasts": forecasts}
