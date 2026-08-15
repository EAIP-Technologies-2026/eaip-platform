"""Operations Analytics API — aggregates operational data from existing EAIP services."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.agents.models import AgentStatus, RunStatus
from eaip.agents.registry import AgentRegistry
from eaip.agents.runtime import AgentRuntime
from eaip.events.store import EventStore
from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.workflow.models import WorkflowStatus
from eaip.workflow.registry import WorkflowRegistry
from eaip.workflow.executor import WorkflowEngine

router = APIRouter(
    prefix="/operations", tags=["operations"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.operations")


def _safe_div(numerator: float, denominator: float) -> float:
    """Safe division that returns 0.0 instead of NaN/Infinity."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _status_text(status: Any) -> str:
    return status.value if hasattr(status, "value") else str(status)


@router.get("/analytics")
async def operations_analytics(request: Request):
    """Aggregated operations analytics from existing platform services."""
    container = request.app.state.lifecycle.platform.container
    agent_reg = container.try_resolve(AgentRegistry)
    agent_runtime = container.try_resolve(AgentRuntime)
    wf_reg = container.try_resolve(WorkflowRegistry)
    wf_engine = container.try_resolve(WorkflowEngine)
    event_store = container.try_resolve(EventStore)

    # --- Agent metrics ---
    total_agents = 0
    running_agents = 0
    idle_agents = 0
    error_agents = 0
    paused_agents = 0
    total_executions = 0
    successful_executions = 0
    failed_executions = 0
    avg_latency_ms = 0.0
    executions_today = 0

    if agent_reg:
        agents = await agent_reg.list_agents()
        total_agents = len(agents)
        for a in agents:
            s = await agent_reg.get_status(a.id)
            if s == AgentStatus.RUNNING:
                running_agents += 1
            elif s == AgentStatus.PAUSED:
                paused_agents += 1
            elif s == AgentStatus.FAILED:
                error_agents += 1
            else:
                idle_agents += 1

    if agent_runtime:
        all_runs = agent_runtime.list_runs()
        total_executions = len(all_runs)
        successful_executions = sum(1 for r in all_runs if r.status == RunStatus.COMPLETED)
        failed_executions = sum(1 for r in all_runs if r.status == RunStatus.FAILED)
        durations = [r.duration_ms for r in all_runs if r.duration_ms > 0]
        avg_latency_ms = sum(durations) / len(durations) if durations else 0.0
        now = datetime.now(UTC)
        executions_today = sum(1 for r in all_runs if r.created_at.date() == now.date())

    agent_success_rate = _safe_div(successful_executions, successful_executions + failed_executions) * 100

    # --- Workflow metrics ---
    total_workflows = 0
    active_workflows = 0
    paused_workflows = 0
    draft_workflows = 0
    wf_total_executions = 0
    wf_successful = 0
    wf_failed = 0
    wf_avg_duration_ms = 0.0
    wf_executions_today = 0

    if wf_reg:
        wfs = await wf_reg.list_definitions()
        total_workflows = len(wfs)
        for w in wfs:
            s = await wf_reg.get_status(w.id)
            if s == WorkflowStatus.RUNNING:
                active_workflows += 1
            elif s == WorkflowStatus.PAUSED:
                paused_workflows += 1
            else:
                draft_workflows += 1

    if wf_engine:
        wf_runs = list((wf_engine._runs or {}).values())
        wf_total_executions = len(wf_runs)
        wf_successful = sum(1 for r in wf_runs if r.status == WorkflowStatus.COMPLETED)
        wf_failed = sum(1 for r in wf_runs if r.status == WorkflowStatus.FAILED)
        durations = [r.duration_ms for r in wf_runs if r.duration_ms > 0]
        wf_avg_duration_ms = sum(durations) / len(durations) if durations else 0.0
        now = datetime.now(UTC)
        wf_executions_today = sum(1 for r in wf_runs if r.created_at.date() == now.date())

    wf_success_rate = _safe_div(wf_successful, wf_successful + wf_failed) * 100

    # --- Event metrics ---
    total_events = 0
    recent_events: list[dict[str, Any]] = []
    if event_store:
        recent = event_store.recent(limit=100)
        total_events = len(recent)
        for e in recent[:20]:
            ev = getattr(e, "event", e)
            payload = getattr(ev, "payload", None)
            if isinstance(payload, dict):
                action = str(payload.get("action", payload.get("event_name", "")))
                message = str(payload.get("message", payload.get("details", "")))
            else:
                action = str(getattr(ev, "action", getattr(ev, "name", "Event")))
                message = str(getattr(ev, "message", ""))
            recent_events.append({
                "id": str(getattr(e, "id", getattr(ev, "id", ""))) or f"evt-{len(recent_events)}",
                "title": action or "Platform Event",
                "description": message,
                "timestamp": getattr(ev, "timestamp", datetime.now(UTC)).isoformat()
                if hasattr(getattr(ev, "timestamp", None), "isoformat")
                else datetime.now(UTC).isoformat(),
                "type": getattr(ev, "type", getattr(ev, "event_type", "info")),
            })

    # --- System health ---
    platform = request.app.state.lifecycle.platform
    report = await platform.health.report()
    children = list(getattr(report, "children", []))
    healthy_services = sum(
        1 for c in children if _status_text(c.status) in ("healthy", "skipped")
    )
    degraded_services = sum(1 for c in children if _status_text(c.status) == "degraded")
    down_services = sum(1 for c in children if _status_text(c.status) == "down")
    total_services = len(children)

    overall_status = "healthy"
    if down_services > 0:
        overall_status = "down"
    elif degraded_services > 0:
        overall_status = "degraded"

    # --- Uptime ---
    start = getattr(request.app.state, "_start_time", None)
    uptime_seconds = 0
    uptime_str = "0s"
    if start:
        uptime_seconds = int(time.time() - start)
        days, rem = divmod(uptime_seconds, 86400)
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
        uptime_str = " ".join(parts)

    # --- Aggregated totals ---
    total_operations = total_executions + wf_total_executions
    total_successful = successful_executions + wf_successful
    total_failed = failed_executions + wf_failed
    overall_success_rate = _safe_div(total_successful, total_successful + total_failed) * 100

    return {
        "overview": {
            "totalOperations": total_operations,
            "successfulOperations": total_successful,
            "failedOperations": total_failed,
            "successRate": round(overall_success_rate, 2),
            "activeOperations": running_agents + active_workflows,
            "uptime": uptime_str,
            "uptimeSeconds": uptime_seconds,
            "overallStatus": overall_status,
        },
        "agents": {
            "total": total_agents,
            "running": running_agents,
            "idle": idle_agents,
            "error": error_agents,
            "paused": paused_agents,
            "totalExecutions": total_executions,
            "successfulExecutions": successful_executions,
            "failedExecutions": failed_executions,
            "successRate": round(agent_success_rate, 2),
            "avgLatencyMs": round(avg_latency_ms, 2),
            "executionsToday": executions_today,
        },
        "workflows": {
            "total": total_workflows,
            "active": active_workflows,
            "paused": paused_workflows,
            "draft": draft_workflows,
            "totalExecutions": wf_total_executions,
            "successfulExecutions": wf_successful,
            "failedExecutions": wf_failed,
            "successRate": round(wf_success_rate, 2),
            "avgDurationMs": round(wf_avg_duration_ms, 2),
            "executionsToday": wf_executions_today,
        },
        "health": {
            "overall": overall_status,
            "totalServices": total_services,
            "healthy": healthy_services,
            "degraded": degraded_services,
            "down": down_services,
        },
        "events": {
            "total": total_events,
            "recent": recent_events,
        },
    }


@router.get("/failures")
async def operations_failures(request: Request, limit: int = 50):
    """Recent operational failures aggregated from event store."""
    container = request.app.state.lifecycle.platform.container
    event_store = container.try_resolve(EventStore)
    failures: list[dict[str, Any]] = []

    if event_store:
        recent = event_store.recent(limit=200)
        for e in recent:
            ev = getattr(e, "event", e)
            payload = getattr(ev, "payload", None)
            event_type = getattr(ev, "type", getattr(ev, "event_type", ""))
            is_failure = False
            severity = "warning"

            if isinstance(payload, dict):
                status_val = str(payload.get("status", ""))
                if status_val in ("failed", "error"):
                    is_failure = True
                    severity = "error"
                action = str(payload.get("action", payload.get("event_name", "")))
                message = str(payload.get("message", payload.get("details", "")))
                source = str(payload.get("source", payload.get("component", "")))
            else:
                action = str(getattr(ev, "action", getattr(ev, "name", "")))
                message = str(getattr(ev, "message", ""))
                source = str(getattr(ev, "source", ""))

            if "fail" in event_type.lower() or "error" in event_type.lower():
                is_failure = True
                severity = "error"

            if is_failure:
                failures.append({
                    "id": str(getattr(e, "id", getattr(ev, "id", ""))) or f"fail-{len(failures)}",
                    "title": action or "Operation Failed",
                    "message": message,
                    "severity": severity,
                    "source": source or "unknown",
                    "timestamp": getattr(ev, "timestamp", datetime.now(UTC)).isoformat()
                    if hasattr(getattr(ev, "timestamp", None), "isoformat")
                    else datetime.now(UTC).isoformat(),
                    "type": event_type,
                })
            if len(failures) >= limit:
                break

    return {"failures": failures, "total": len(failures)}


@router.get("/health")
async def operations_health(request: Request):
    """System health breakdown for operations analytics."""
    platform = request.app.state.lifecycle.platform
    report = await platform.health.report()
    children = list(getattr(report, "children", []))

    services = []
    for c in children:
        status = _status_text(c.status)
        services.append({
            "name": c.component,
            "status": status,
            "message": c.message,
        })

    healthy = sum(1 for s in services if s["status"] in ("healthy", "skipped"))
    degraded = sum(1 for s in services if s["status"] == "degraded")
    down = sum(1 for s in services if s["status"] == "down")

    overall = "healthy"
    if down > 0:
        overall = "down"
    elif degraded > 0:
        overall = "degraded"

    return {
        "overall": overall,
        "services": services,
        "summary": {
            "total": len(services),
            "healthy": healthy,
            "degraded": degraded,
            "down": down,
        },
    }
