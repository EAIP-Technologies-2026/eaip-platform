from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/health-center", tags=["health-center"])

_incidents: list[dict[str, Any]] = []


@router.get("/health")
async def platform_health(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.health.reporter import HealthReporter
    reporter = request.app.state.lifecycle.platform.container.try_resolve(HealthReporter)
    if reporter:
        report = await reporter.report()
        status = report.status.value if hasattr(report.status, "value") else str(report.status)
        checks = [{"component": c.component, "status": c.status.value if hasattr(c.status, "value") else str(c.status), "message": c.message} for c in (report.children or [])]
        overall = status
        return {"tenant_id": tenant_id, "overall": overall, "checks": checks, "status": status}
    return {"tenant_id": tenant_id, "overall": "unknown", "checks": [], "status": "unknown"}


@router.get("/incidents")
async def list_incidents(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [i for i in _incidents if i.get("tenant_id") == tenant_id]


@router.post("/incidents", status_code=201)
async def create_incident(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"incident_id": body.get("incident_id") or f"inc-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "severity": str(body.get("severity", "medium")), "title": str(body.get("title", "incident")), "status": "open", "affected_resources": body.get("affected_resources") or [], "created_at": datetime.now(UTC).isoformat()}
    _incidents.append(rec)
    return rec


@router.post("/incidents/{incident_id}/acknowledge")
async def ack_incident(request: Request, incident_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    for inc in _incidents:
        if inc["incident_id"] == incident_id and inc["tenant_id"] == tenant_id:
            inc["status"] = "acknowledged"
            inc["acknowledged_at"] = datetime.now(UTC).isoformat()
            return inc
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="incident not found")


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(request: Request, incident_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    for inc in _incidents:
        if inc["incident_id"] == incident_id and inc["tenant_id"] == tenant_id:
            inc["status"] = "resolved"
            inc["resolved_at"] = datetime.now(UTC).isoformat()
            inc["root_cause"] = str((body or {}).get("root_cause", ""))
            return inc
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="incident not found")
