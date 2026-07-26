from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request

from eaip.agents.registry import AgentRegistry
from eaip.events.store import EventStore
from eaip.knowledge.engine import KnowledgeEngine
from eaip.logging.context import get_logger
from eaip.workflow.registry import WorkflowRegistry
from eaip.runtime.mission import MissionRegistry

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
log = get_logger("eaip.http.routers.monitoring_routes")


@router.get("/health")
async def monitoring_health(request: Request):
    platform = request.app.state.lifecycle.platform
    report = await platform.health.report()
    children = list(getattr(report, "children", []))
    return [
        {
            "name": c.component,
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            "uptime": "0s",
            "responseTime": 0,
            "version": "0.0.2",
        }
        for c in children
    ] or [{"name": "platform", "status": "healthy", "uptime": "0s", "responseTime": 0, "version": "0.0.2"}]


@router.get("/metrics")
async def monitoring_metrics(request: Request):
    container = request.app.state.lifecycle.platform.container
    agent_reg = container.try_resolve(AgentRegistry)
    wf_reg = container.try_resolve(WorkflowRegistry)
    mission_reg = container.try_resolve(MissionRegistry)
    knowledge_eng = container.try_resolve(KnowledgeEngine)

    agent_count = 0
    workflow_count = 0
    mission_count = 0
    doc_count = 0

    if agent_reg:
        agents = await agent_reg.list_agents()
        agent_count = len(agents)
    if wf_reg:
        wfs = await wf_reg.list_definitions()
        workflow_count = len(wfs)
    if mission_reg:
        missions = await mission_reg.list_missions()
        mission_count = len(missions)
    if knowledge_eng:
        try:
            h = await knowledge_eng.health()
            doc_count = h.get("collections", 0) if isinstance(h, dict) else 0
        except Exception:
            pass

    start = getattr(request.app.state, "_start_time", None)
    uptime_str = "0s"
    if start:
        elapsed = int(time.time() - start)
        days, rem = divmod(elapsed, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        uptime_str = " ".join(parts)

    return [
        {"label": "Active Agents", "value": str(agent_count), "unit": "", "change": 0, "trend": "stable"},
        {"label": "Workflows", "value": str(workflow_count), "unit": "", "change": 0, "trend": "stable"},
        {"label": "Missions", "value": str(mission_count), "unit": "", "change": 0, "trend": "stable"},
        {"label": "Knowledge Collections", "value": str(doc_count), "unit": "", "change": 0, "trend": "stable"},
        {"label": "Uptime", "value": uptime_str, "unit": "", "change": 0, "trend": "stable"},
    ]


@router.get("/logs")
async def monitoring_logs(request: Request, limit: int = 50, level: str = "", source: str = ""):
    return [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "info",
            "message": "Monitoring endpoint active",
            "source": "eaip.monitoring",
        }
    ]


@router.get("/alerts")
async def monitoring_alerts(request: Request):
    return []


@router.get("/queues")
async def monitoring_queues(request: Request):
    return []


@router.get("/diagnostics")
async def monitoring_diagnostics(request: Request):
    platform = request.app.state.lifecycle.platform
    report = await platform.health.report()
    children = list(getattr(report, "children", []))
    checks = []
    for c in children:
        checks.append({
            "name": c.component,
            "status": "passed" if c.status.value in ("healthy",) else "warning",
            "message": c.message,
            "duration": 0,
        })
    if not checks:
        checks.append({"name": "platform", "status": "passed", "message": "Platform is running", "duration": 0})
    return {
        "checks": checks,
        "lastRun": datetime.now(timezone.utc).isoformat(),
        "passed": sum(1 for c in checks if c["status"] == "passed"),
        "failed": sum(1 for c in checks if c["status"] != "passed"),
    }


@router.get("/events")
async def monitoring_events(request: Request, limit: int = 50):
    store = request.app.state.lifecycle.platform.container.try_resolve(EventStore)
    if store is not None:
        return store.recent(limit=limit)
    return []
