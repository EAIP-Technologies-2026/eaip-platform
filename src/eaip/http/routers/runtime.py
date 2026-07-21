from __future__ import annotations

import time
from datetime import datetime, timezone

import psutil
from fastapi import APIRouter, Depends, Request

from eaip.agents.registry import AgentRegistry
from eaip.agents.runtime import AgentRuntime
from eaip.http.dependencies import get_current_user
from eaip.knowledge.engine import KnowledgeEngine
from eaip.logging.context import get_logger
from eaip.metrics.metrics import Meter
from eaip.runtime.mission import MissionRegistry, MissionStatus
from eaip.workflow.registry import WorkflowRegistry

router = APIRouter(prefix="/runtime", tags=["runtime"])
log = get_logger("eaip.http.routers.runtime")


def _format_uptime(seconds: float) -> str:
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def _get_uptime(request: Request) -> str:
    start = getattr(request.app.state, "_start_time", None)
    if start is None:
        return "0s"
    return _format_uptime(time.time() - start)


@router.get("/metrics")
async def runtime_metrics(request: Request, _user: dict = Depends(get_current_user)):
    platform = request.app.state.lifecycle.platform
    container = platform.container
    agent_reg = container.try_resolve(AgentRegistry)
    wf_reg = container.try_resolve(WorkflowRegistry)
    mission_reg = container.try_resolve(MissionRegistry)
    knowledge_eng = container.try_resolve(KnowledgeEngine)

    running_agents = 0
    total_agents = 0
    running_workflows = 0
    total_workflows = 0
    running_missions = 0
    total_missions = 0
    knowledge_jobs = 0

    if agent_reg:
        agents = await agent_reg.list_agents()
        total_agents = len(agents)
        for a in agents:
            s = await agent_reg.get_status(a.id)
            if s and s.value == "running":
                running_agents += 1

    if wf_reg:
        wfs = await wf_reg.list_definitions()
        total_workflows = len(wfs)
        for w in wfs:
            s = await wf_reg.get_status(w.id)
            if s and s.value == "running":
                running_workflows += 1

    if mission_reg:
        missions = await mission_reg.list_missions()
        total_missions = len(missions)
        running_missions = sum(1 for m in missions if m.status == MissionStatus.RUNNING)

    if knowledge_eng:
        try:
            h = await knowledge_eng.health()
            knowledge_jobs = h.get("collections", 0) if isinstance(h, dict) else 0
        except Exception:
            pass

    mem = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=None)

    return {
        "cpuPercent": cpu_pct,
        "memoryPercent": mem.percent,
        "memoryUsed": f"{mem.used // (1024 * 1024)} MB",
        "memoryTotal": f"{mem.total // (1024 * 1024)} MB",
        "avgLatencyMs": 0,
        "eventThroughput": 0,
        "runningAgents": running_agents,
        "runningWorkflows": running_workflows,
        "knowledgeJobs": knowledge_jobs,
        "activeUsers": 0,
        "uptime": _get_uptime(request),
    }


@router.get("/health")
async def runtime_health(request: Request, _user: dict = Depends(get_current_user)):
    platform = request.app.state.lifecycle.platform
    reporter = platform.health
    uptime_str = _get_uptime(request)
    report = await reporter.report()
    if hasattr(report, "children") and report.children:
        return [
            {
                "service": c.component,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                "uptime": uptime_str,
                "version": "0.0.2",
                "message": c.message,
                "lastChecked": datetime.now(timezone.utc).isoformat(),
            }
            for c in report.children
        ]
    return [
        {
            "service": "platform",
            "status": report.status.value if hasattr(report.status, "value") else str(report.status),
            "uptime": uptime_str,
            "version": "0.0.2",
            "message": report.message,
            "lastChecked": datetime.now(timezone.utc).isoformat(),
        }
    ]


@router.get("/status")
async def runtime_status(request: Request, _user: dict = Depends(get_current_user)):
    platform = request.app.state.lifecycle.platform
    container = platform.container
    uptime_str = _get_uptime(request)
    services_status = []
    for key in container.keys():
        key_str = str(key)
        skip_types = {"str", "int", "float", "bool", "dict", "list", "tuple", "set"}
        if key.__module__.startswith("eaip") and key.__name__ not in skip_types:
            try:
                instance = container.try_resolve(key)
                services_status.append({
                    "service": key.__name__,
                    "status": "healthy" if instance is not None else "unhealthy",
                    "uptime": uptime_str,
                    "version": "0.0.2",
                })
            except Exception:
                services_status.append({
                    "service": key.__name__,
                    "status": "unknown",
                    "uptime": uptime_str,
                    "version": "0.0.2",
                })
    return services_status[:50]
