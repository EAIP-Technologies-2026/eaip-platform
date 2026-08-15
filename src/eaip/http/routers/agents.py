from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any

import psutil
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.agents.models import AgentSpec, AgentStatus, Goal, RunStatus
from eaip.agents.registry import AgentRegistry
from eaip.agents.runtime import AgentRuntime
from eaip.events.store import EventStore
from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(prefix="/agents", tags=["agents"])
log = get_logger("eaip.http.routers.agents")


def _fmt_uptime(seconds: float) -> str:
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def _get_registry(request: Request) -> AgentRegistry:
    return request.app.state.lifecycle.platform.container.resolve(AgentRegistry)


def _get_runtime(request: Request) -> AgentRuntime | None:
    return request.app.state.lifecycle.platform.container.try_resolve(AgentRuntime)


def _agent_to_summary(agent: AgentSpec, status: str | None = None) -> dict[str, Any]:
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "status": status or "idle",
        "model": agent.llm_adapter or "default",
        "labels": list(agent.tools),
        "tags": [],
        "owner": "",
        "createdAt": datetime.now(UTC).isoformat(),
        "updatedAt": datetime.now(UTC).isoformat(),
        "metrics": {"totalRuns": 0, "successRate": 0, "avgDurationMs": 0},
    }


def _agent_to_detail(
    agent: AgentSpec, status: str | None = None, metadata: dict | None = None
) -> dict[str, Any]:
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "status": status or "idle",
        "model": agent.llm_adapter or "default",
        "systemPrompt": (metadata or {}).get("system_prompt", ""),
        "tools": [
            {"id": t, "name": t, "description": "", "enabled": True, "type": "tool"}
            for t in agent.tools
        ],
        "knowledge": [],
        "memory": [],
        "config": {},
        "labels": list(agent.tools),
        "tags": [],
        "owner": (metadata or {}).get("owner", ""),
        "createdAt": datetime.now(UTC).isoformat(),
        "updatedAt": datetime.now(UTC).isoformat(),
        "metrics": {
            "totalRuns": 0,
            "successRate": 0,
            "avgDurationMs": 0,
            "totalTokens": 0,
            "totalLatencyMs": 0,
        },
    }


@router.get("/health")
async def agent_health(request: Request, _user: dict = Depends(get_current_user)):
    runtime = _get_runtime(request)
    if runtime is None:
        return {
            "status": "healthy",
            "uptime": "0s",
            "activeAgents": 0,
            "totalAgents": 0,
            "avgLatencyMs": 0,
            "throughputPerMin": 0,
            "tokensUsedTotal": 0,
            "memoryUsagePercent": 0,
        }
    health = await runtime.health()
    all_runs = runtime.list_runs()
    durations = [r.duration_ms for r in all_runs if r.duration_ms > 0]
    avg_latency = sum(durations) / len(durations) if durations else 0
    now = datetime.now(UTC)
    exec_today = sum(1 for r in all_runs if r.created_at.date() == now.date())
    start = getattr(request.app.state, "_start_time", None)
    uptime_str = _fmt_uptime(time.time() - start) if start else "0s"
    mem = psutil.virtual_memory()
    return {
        "status": health.status.value,
        "uptime": uptime_str,
        "activeAgents": health.details.get("active_runs", 0),
        "totalAgents": health.details.get("total_runs", 0),
        "avgLatencyMs": round(avg_latency, 2),
        "throughputPerMin": exec_today,
        "tokensUsedTotal": 0,
        "memoryUsagePercent": mem.percent,
    }


@router.get("/stats")
async def agent_stats(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    runtime = _get_runtime(request)
    agents = await registry.list_agents()
    total = len(agents)
    running = 0
    idle = 0
    error_count = 0
    paused = 0
    for a in agents:
        s = await registry.get_status(a.id)
        if s == AgentStatus.RUNNING:
            running += 1
        elif s == AgentStatus.PAUSED:
            paused += 1
        elif s == AgentStatus.FAILED:
            error_count += 1
        else:
            idle += 1
    total_executions = sum(len(runtime.list_runs(agent_id=a.id)) for a in agents) if runtime else 0
    all_runs = runtime.list_runs() if runtime else []
    durations = [r.duration_ms for r in all_runs if r.duration_ms > 0]
    avg_latency = sum(durations) / len(durations) if durations else 0
    completed = sum(1 for r in all_runs if r.status == RunStatus.COMPLETED)
    failed = sum(1 for r in all_runs if r.status == RunStatus.FAILED)
    total_completed_failed = completed + failed
    success_rate = (completed / total_completed_failed * 100) if total_completed_failed > 0 else 0
    now = datetime.now(UTC)
    exec_today = sum(1 for r in all_runs if r.created_at.date() == now.date())
    return {
        "totalAgents": total,
        "runningAgents": running,
        "idleAgents": idle,
        "errorAgents": error_count,
        "pausedAgents": paused,
        "totalExecutions": total_executions,
        "successRate": round(success_rate, 2),
        "avgLatencyMs": round(avg_latency, 2),
        "avgTokensPerRun": 0,
        "executionsToday": exec_today,
        "activeUsers": 0,
    }


@router.get("")
async def list_agents(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    agents = await registry.list_agents()
    result = []
    for a in agents:
        s = await registry.get_status(a.id)
        result.append(_agent_to_summary(a, s.value if s else None))
    return result


@router.post("")
async def create_agent(
    request: Request, body: dict[str, Any], _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    agent_id = body.get("id", f"agent-{uuid.uuid4().hex[:8]}")
    agent = AgentSpec(
        id=agent_id,
        name=body.get("name", "New Agent"),
        description=body.get("description", ""),
        tools=tuple(body.get("tools", [])),
        llm_adapter=body.get("model", ""),
    )
    created = await registry.create(agent, body.get("metadata"))
    return _agent_to_summary(created, AgentStatus.DRAFT.value)


@router.get("/{agent_id}")
async def get_agent(request: Request, agent_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    agent = await registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")
    status = await registry.get_status(agent_id)
    metadata = await registry.get_metadata(agent_id)
    return _agent_to_detail(agent, status.value if status else None, metadata)


@router.put("/{agent_id}")
async def update_agent(
    request: Request, agent_id: str, body: dict[str, Any], _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    updates = {}
    for field in ("name", "description", "tools", "llm_adapter", "version", "max_steps"):
        if field in body:
            updates[field] = tuple(body[field]) if field == "tools" else body[field]
    try:
        updated = await registry.update(agent_id, **updates)
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    status = await registry.get_status(agent_id)
    return _agent_to_summary(updated, status.value if status else None)


@router.delete("/{agent_id}")
async def delete_agent(request: Request, agent_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    try:
        await registry.delete(agent_id)
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    return {"status": "ok"}


@router.post("/{agent_id}/archive")
async def archive_agent(request: Request, agent_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    try:
        await registry.transition_to(agent_id, AgentStatus.ARCHIVED)
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    return {"status": "ok"}


@router.post("/{agent_id}/duplicate")
async def duplicate_agent(request: Request, agent_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    agent = await registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")
    new_id = f"{agent_id}-copy-{uuid.uuid4().hex[:4]}"
    new_agent = agent.model_copy(update={"id": new_id, "name": f"{agent.name} (Copy)"})
    created = await registry.create(new_agent)
    return _agent_to_summary(created)


@router.post("/{agent_id}/execute")
async def execute_agent(
    request: Request, agent_id: str, body: dict[str, Any], _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    runtime = _get_runtime(request)
    agent = await registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")
    if runtime is None:
        return {
            "id": f"run-{uuid.uuid4().hex[:8]}",
            "agentId": agent_id,
            "status": "completed",
            "input": body.get("input", ""),
            "output": "Execution simulated (no runtime configured)",
            "startedAt": datetime.now(UTC).isoformat(),
            "completedAt": datetime.now(UTC).isoformat(),
            "duration": 0,
        }
    await registry.transition_to(agent_id, AgentStatus.RUNNING)
    goal = Goal(text=body.get("input", ""))
    run = await runtime.create_run(agent, goal)
    completed = await runtime.start_run(run.id)
    await registry.transition_to(agent_id, AgentStatus.READY)
    return {
        "id": completed.id,
        "agentId": agent_id,
        "status": completed.status.value,
        "input": body.get("input", ""),
        "output": completed.result or "",
        "startedAt": completed.created_at.isoformat(),
        "completedAt": completed.completed_at.isoformat() if completed.completed_at else None,
        "duration": completed.duration_ms,
    }


@router.get("/{agent_id}/executions")
async def list_agent_executions(
    request: Request, agent_id: str, _user: dict = Depends(get_current_user)
):
    runtime = _get_runtime(request)
    if runtime is None:
        return []
    runs = runtime.list_runs(agent_id=agent_id)
    return [
        {
            "id": r.id,
            "agentId": r.agent_id,
            "status": r.status.value,
            "input": r.goal.text,
            "output": r.result,
            "startedAt": r.created_at.isoformat(),
            "completedAt": r.completed_at.isoformat() if r.completed_at else None,
            "duration": r.duration_ms,
        }
        for r in runs
    ]


@router.get("/{agent_id}/events")
async def list_agent_events(
    request: Request, agent_id: str, limit: int = 50, _user: dict = Depends(get_current_user)
):
    store = request.app.state.lifecycle.platform.container.try_resolve(EventStore)
    if store is not None:
        return store.recent_by(agent_id=agent_id, limit=limit)
    return []


@router.post("/{agent_id}/executions/{execution_id}/pause")
async def pause_agent_execution(
    request: Request, agent_id: str, execution_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    runtime = _get_runtime(request)
    if runtime:
        await runtime.cancel_run(execution_id)
    await registry.transition_to(agent_id, AgentStatus.PAUSED)
    return {"status": "ok"}


@router.post("/{agent_id}/executions/{execution_id}/resume")
async def resume_agent_execution(
    request: Request, agent_id: str, execution_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    await registry.transition_to(agent_id, AgentStatus.READY)
    return {"status": "ok"}


@router.post("/{agent_id}/executions/{execution_id}/stop")
async def stop_agent_execution(
    request: Request, agent_id: str, execution_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    runtime = _get_runtime(request)
    if runtime:
        await runtime.cancel_run(execution_id)
    await registry.transition_to(agent_id, AgentStatus.STOPPED)
    return {"status": "ok"}


@router.post("/{agent_id}/executions/{execution_id}/retry")
async def retry_agent_execution(
    request: Request, agent_id: str, execution_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    runtime = _get_runtime(request)
    agent = await registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")
    if runtime is None:
        return {
            "id": f"run-{uuid.uuid4().hex[:8]}",
            "agentId": agent_id,
            "status": "completed",
            "input": "",
            "output": "Retry simulated",
            "startedAt": datetime.now(UTC).isoformat(),
            "completedAt": datetime.now(UTC).isoformat(),
            "duration": 0,
        }
    goal = Goal(text="retry")
    run = await runtime.create_run(agent, goal)
    completed = await runtime.start_run(run.id)
    await registry.transition_to(agent_id, AgentStatus.READY)
    return {
        "id": completed.id,
        "agentId": agent_id,
        "status": completed.status.value,
        "input": "",
        "output": completed.result or "",
        "startedAt": completed.created_at.isoformat(),
        "completedAt": completed.completed_at.isoformat() if completed.completed_at else None,
        "duration": completed.duration_ms,
    }
