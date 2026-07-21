from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from eaip.logging.context import get_logger

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
log = get_logger("eaip.http.routers.monitoring")


@router.get("/health")
async def monitoring_health(request: Request):
    lifecycle = request.app.state.lifecycle
    reporter = lifecycle.platform.health
    report = await reporter.report()
    if hasattr(report, "children"):
        return [
            {
                "name": c.component,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                "uptime": "0s",
                "responseTime": 0,
            }
            for c in report.children
        ]
    return [
        {
            "name": "platform",
            "status": report.status.value if hasattr(report.status, "value") else str(report.status),
            "uptime": "0s",
            "responseTime": 0,
        }
    ]


@router.get("/metrics")
async def monitoring_metrics(request: Request):
    lifecycle = request.app.state.lifecycle
    container = lifecycle.platform.container
    meter = container.try_resolve("Meter")
    return [
        {"label": "Active Services", "value": "8", "unit": "", "change": 0},
        {"label": "Total Requests", "value": "0", "unit": "", "change": 0},
        {"label": "Error Rate", "value": "0%", "unit": "%", "change": 0},
        {"label": "Avg Response", "value": "0ms", "unit": "ms", "change": 0},
        {"label": "Active Agents", "value": "0", "unit": "", "change": 0},
        {"label": "Uptime", "value": "0s", "unit": "", "change": 0},
    ]


@router.get("/logs")
async def monitoring_logs(request: Request, limit: int = 50):
    return [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "info",
            "message": "Monitoring endpoint active",
            "source": "eaip.monitoring",
        }
    ]
