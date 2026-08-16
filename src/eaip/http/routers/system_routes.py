"""System and platform overview endpoints consumed by the Enterprise Console UI."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.events.store import EventStore
from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.organization.service import OrganizationService

router = APIRouter(tags=["system"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.system")


def _status_text(status: Any) -> str:
    return status.value if hasattr(status, "value") else str(status)


@router.get("/system/health")
async def system_health(request: Request) -> dict[str, Any]:
    """Aggregated system health in the shape expected by the console health page."""
    platform = request.app.state.lifecycle.platform
    report = await platform.health.report()
    children = list(getattr(report, "children", []))

    start = getattr(request.app.state, "_start_time", None)
    uptime = "0s"
    if start:
        elapsed = int(time.time() - start)
        days, rem = divmod(elapsed, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        uptime = " ".join(parts)

    services: list[dict[str, Any]] = [
        {
            "name": c.component,
            "status": _status_text(c.status),
            "uptime": uptime,
            "latency": "0ms",
            "message": c.message,
        }
        for c in children
    ]
    if not services:
        services.append(
            {
                "name": "platform",
                "status": "healthy",
                "uptime": uptime,
                "latency": "0ms",
                "message": "Platform running",
            }
        )

    overall = report.status.value if hasattr(report.status, "value") else str(report.status)
    if overall in ("healthy", "skipped"):
        overall = "healthy"
    elif overall == "degraded":
        overall = "degraded"
    else:
        overall = "down"

    return {
        "overall": overall,
        "uptime": uptime,
        "services": services,
        "metrics": [
            {
                "label": "Services",
                "value": len(services),
                "unit": "",
                "threshold": 0,
                "status": "healthy",
            },
            {
                "label": "Background Tasks",
                "value": 2,
                "unit": "",
                "threshold": 0,
                "status": "healthy",
            },
        ],
    }


@router.get("/admin/health")
async def admin_health(request: Request) -> dict[str, Any]:
    """Detailed operational health endpoint for the admin platform."""
    from eaip.healthagg.aggregator import HealthAggregator
    from eaip.operations.health import OperationsHealthCheck
    
    container = request.app.state.lifecycle.platform.container
    agg = container.try_resolve(HealthAggregator)
    
    platform = request.app.state.lifecycle.platform
    report = await platform.health.report()
    children = list(getattr(report, "children", []))
    
    # Check for operations
    ops_check = next((c for c in children if c.component == "eaip.operations"), None)
    
    return {
        "status": report.status.value if hasattr(report.status, "value") else str(report.status),
        "timestamp": datetime.now(UTC).isoformat(),
        "components": [
            {
                "id": c.component,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                "message": c.message,
                "metadata": getattr(c, "metadata", {})
            }
            for c in children
        ],
        "dependencies": agg.dependency_graph.get_all_nodes() if agg else [],
        "operations_status": ops_check.status.value if ops_check and hasattr(ops_check.status, "value") else "unknown"
    }


@router.get("/system/metrics")
async def system_metrics(request: Request) -> list[dict[str, Any]]:
    """Health metrics in the shape expected by the console health page."""
    platform = request.app.state.lifecycle.platform
    report = await platform.health.report()
    children = list(getattr(report, "children", []))

    healthy = sum(1 for c in children if _status_text(c.status) in ("healthy", "skipped"))
    degraded = sum(1 for c in children if _status_text(c.status) == "degraded")
    down = sum(1 for c in children if _status_text(c.status) == "down")

    return [
        {
            "label": "Healthy Services",
            "value": healthy,
            "unit": "",
            "threshold": 0,
            "status": "healthy",
        },
        {
            "label": "Degraded",
            "value": degraded,
            "unit": "",
            "threshold": 1,
            "status": "warning" if degraded else "healthy",
        },
        {
            "label": "Down",
            "value": down,
            "unit": "",
            "threshold": 1,
            "status": "critical" if down else "healthy",
        },
        {
            "label": "Components",
            "value": len(children),
            "unit": "",
            "threshold": 0,
            "status": "healthy",
        },
    ]


@router.get("/users")
async def list_users(request: Request) -> dict[str, Any]:
    """User directory consumed by the Enterprise Console users page."""
    org_svc = request.app.state.lifecycle.platform.container.try_resolve(OrganizationService)
    members = []
    if org_svc is not None and hasattr(org_svc, "list_members"):
        try:
            members = org_svc.list_members()
        except Exception:
            members = []

    items: list[dict[str, Any]] = []
    for m in members:
        uid = getattr(m, "user_id", getattr(m, "id", ""))
        items.append(
            {
                "id": uid,
                "name": getattr(m, "name", getattr(m, "display_name", uid)),
                "email": getattr(m, "email", ""),
                "roles": [getattr(m, "role", "member")] if hasattr(m, "role") else ["member"],
                "status": getattr(m, "status", "active"),
            }
        )

    if not items:
        items = [
            {
                "id": "admin",
                "name": "Administrator",
                "email": "admin@eaip.io",
                "roles": ["admin", "user"],
                "status": "active",
            }
        ]

    return {"items": items, "total": len(items)}


@router.get("/activity")
async def list_activity(request: Request, limit: int = 50) -> list[dict[str, Any]]:
    """Recent platform activity feed consumed by the Enterprise Console activity page."""
    store = request.app.state.lifecycle.platform.container.try_resolve(EventStore)
    items: list[dict[str, Any]] = []
    if store is not None:
        recent = store.recent(limit=limit)
        for e in recent:
            ev = getattr(e, "event", e)
            payload = getattr(ev, "payload", None)
            if isinstance(payload, dict):
                action = str(payload.get("action", payload.get("event_name", "")))
                message = str(payload.get("message", payload.get("details", "")))
            else:
                action = str(getattr(ev, "action", getattr(ev, "name", "Event")))
                message = str(getattr(ev, "message", ""))
            items.append(
                {
                    "id": str(getattr(e, "id", getattr(ev, "id", ""))) or f"evt-{len(items)}",
                    "title": action or "Platform Event",
                    "description": message,
                    "timestamp": getattr(ev, "timestamp", datetime.now(UTC)).isoformat()
                    if hasattr(getattr(ev, "timestamp", None), "isoformat")
                    else datetime.now(UTC).isoformat(),
                    "type": getattr(ev, "type", getattr(ev, "event_type", "info")),
                    "actor": getattr(ev, "actor", getattr(ev, "user_id", None)),
                }
            )
    return items
