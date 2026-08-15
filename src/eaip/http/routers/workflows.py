from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.events.store import EventStore
from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.workflow.executor import WorkflowEngine
from eaip.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowStatus, WorkflowStep
from eaip.workflow.registry import WorkflowRegistry

router = APIRouter(prefix="/workflows", tags=["workflows"])
log = get_logger("eaip.http.routers.workflows")


def _get_registry(request: Request) -> WorkflowRegistry:
    return request.app.state.lifecycle.platform.container.resolve(WorkflowRegistry)


def _get_engine(request: Request) -> WorkflowEngine | None:
    return request.app.state.lifecycle.platform.container.try_resolve(WorkflowEngine)


def _wf_to_summary(wf: WorkflowDefinition, status: str | None = None) -> dict[str, Any]:
    return {
        "id": wf.id,
        "name": wf.name,
        "description": getattr(wf, "description", ""),
        "status": status or "draft",
        "triggers": str(len(getattr(wf, "triggers", ()))),
        "labels": [],
        "tags": [],
        "owner": "",
        "createdAt": datetime.now(UTC).isoformat(),
        "updatedAt": datetime.now(UTC).isoformat(),
    }


@router.get("/health")
async def workflow_health(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    engine = _get_engine(request)
    wfs = await registry.list_definitions()
    total = len(wfs)
    active = (
        sum(1 for r in (engine._runs or {}).values() if r.status == WorkflowStatus.RUNNING)
        if engine
        else 0
    )
    now = datetime.now(UTC)
    wf_runs = list((engine._runs or {}).values())
    durations = [r.duration_ms for r in wf_runs if r.duration_ms > 0]
    avg_duration = sum(durations) / len(durations) if durations else 0
    completed = sum(1 for r in wf_runs if r.status == WorkflowStatus.COMPLETED)
    failed = sum(1 for r in wf_runs if r.status == WorkflowStatus.FAILED)
    completed_failed = completed + failed
    success_rate = (completed / completed_failed * 100) if completed_failed > 0 else 0
    exec_today = sum(1 for r in wf_runs if r.created_at.date() == now.date())
    failed_today = sum(
        1
        for r in wf_runs
        if r.status == WorkflowStatus.FAILED and r.created_at.date() == now.date()
    )
    return {
        "status": "healthy",
        "activeWorkflows": active,
        "totalWorkflows": total,
        "executionsToday": exec_today,
        "successRate": round(success_rate, 2),
        "avgDurationMs": round(avg_duration, 2),
        "failedToday": failed_today,
    }


@router.get("/stats")
async def workflow_stats(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    engine = _get_engine(request)
    wfs = await registry.list_definitions()
    total = len(wfs)
    active_count = 0
    paused_count = 0
    draft_count = 0
    archived_count = 0
    for w in wfs:
        s = await registry.get_status(w.id)
        if s == WorkflowStatus.RUNNING:
            active_count += 1
        elif s == WorkflowStatus.PAUSED:
            paused_count += 1
        elif s == WorkflowStatus.ARCHIVED:
            archived_count += 1
        else:
            draft_count += 1
    total_executions = len(engine._runs) if engine else 0
    now = datetime.now(UTC)
    wf_runs = list((engine._runs or {}).values())
    durations = [r.duration_ms for r in wf_runs if r.duration_ms > 0]
    avg_duration = sum(durations) / len(durations) if durations else 0
    completed = sum(1 for r in wf_runs if r.status == WorkflowStatus.COMPLETED)
    failed = sum(1 for r in wf_runs if r.status == WorkflowStatus.FAILED)
    completed_failed = completed + failed
    success_rate = (completed / completed_failed * 100) if completed_failed > 0 else 0
    exec_today = sum(1 for r in wf_runs if r.created_at.date() == now.date())
    failed_today = sum(
        1
        for r in wf_runs
        if r.status == WorkflowStatus.FAILED and r.created_at.date() == now.date()
    )
    return {
        "totalWorkflows": total,
        "activeCount": active_count,
        "pausedCount": paused_count,
        "draftCount": draft_count,
        "archivedCount": archived_count,
        "totalExecutions": total_executions,
        "successRate": round(success_rate, 2),
        "avgDurationMs": round(avg_duration, 2),
        "executionsToday": exec_today,
        "failedToday": failed_today,
    }


@router.get("")
async def list_workflows(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    wfs = await registry.list_definitions()
    result = []
    for w in wfs:
        s = await registry.get_status(w.id)
        result.append(_wf_to_summary(w, s.value if s else None))
    return result


@router.post("")
async def create_workflow(
    request: Request, body: dict[str, Any], _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    wf_id = body.get("id", f"wf-{uuid.uuid4().hex[:8]}")
    steps = tuple(
        WorkflowStep(
            id=s.get("id", f"step-{i}"),
            name=s.get("name", f"Step {i}"),
            agent_id=s.get("agent_id", ""),
            tool_name=s.get("tool_name", ""),
            prompt=s.get("prompt", ""),
            input=s.get("input", {}),
            timeout_seconds=s.get("timeout_seconds", 0.0),
        )
        for i, s in enumerate(body.get("steps", body.get("nodes", [])))
    )
    edges = tuple(
        WorkflowEdge(
            source_id=e.get("source", e.get("source_id", "")),
            target_id=e.get("target", e.get("target_id", "")),
            label=e.get("label", ""),
        )
        for e in body.get("edges", body.get("connections", []))
    )
    wf = WorkflowDefinition(
        id=wf_id,
        name=body.get("name", "New Workflow"),
        description=body.get("description", ""),
        steps=steps,
        edges=edges,
        version=body.get("version", "0.1.0"),
    )
    created = await registry.create(wf, body.get("metadata"))
    return _wf_to_summary(created, WorkflowStatus.PENDING.value)


@router.get("/{workflow_id}")
async def get_workflow(request: Request, workflow_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    wf = await registry.get(workflow_id)
    if wf is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id} not found"
        )
    s = await registry.get_status(workflow_id)
    return {
        "id": wf.id,
        "name": wf.name,
        "description": getattr(wf, "description", ""),
        "status": s.value if s else "draft",
        "nodes": [
            {
                "id": s.id,
                "type": s.type,
                "label": s.name,
                "x": 0,
                "y": 0,
                "config": {"agent_id": s.agent_id, "tool_name": s.tool_name, "prompt": s.prompt},
            }
            for s in wf.steps
        ],
        "connections": [
            {
                "id": f"conn-{i}",
                "source": e.source_id,
                "target": e.target_id,
                "label": e.label,
                "condition": e.condition.value,
            }
            for i, e in enumerate(wf.edges)
        ],
        "createdAt": datetime.now(UTC).isoformat(),
        "updatedAt": datetime.now(UTC).isoformat(),
    }


@router.put("/{workflow_id}")
async def update_workflow(
    request: Request,
    workflow_id: str,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    registry = _get_registry(request)
    updates = {}
    for field in ("name", "description", "version"):
        if field in body:
            updates[field] = body[field]
    if "steps" in body or "nodes" in body:
        steps_data = body.get("steps", body.get("nodes", []))
        updates["steps"] = tuple(
            WorkflowStep(
                id=s.get("id", f"step-{i}"),
                name=s.get("name", f"Step {i}"),
                agent_id=s.get("agent_id", ""),
                tool_name=s.get("tool_name", ""),
                prompt=s.get("prompt", ""),
                input=s.get("input", {}),
                timeout_seconds=s.get("timeout_seconds", 0.0),
            )
            for i, s in enumerate(steps_data)
        )
    if "edges" in body or "connections" in body:
        edges_data = body.get("edges", body.get("connections", []))
        updates["edges"] = tuple(
            WorkflowEdge(
                source_id=e.get("source", e.get("source_id", "")),
                target_id=e.get("target", e.get("target_id", "")),
                label=e.get("label", ""),
            )
            for e in edges_data
        )
    try:
        updated = await registry.update(workflow_id, **updates)
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    return _wf_to_summary(updated)


@router.delete("/{workflow_id}")
async def delete_workflow(
    request: Request, workflow_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    try:
        await registry.delete(workflow_id)
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    return {"status": "ok"}


@router.post("/{workflow_id}/archive")
async def archive_workflow(
    request: Request, workflow_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    try:
        await registry.archive(workflow_id)
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    return {"status": "ok"}


@router.post("/{workflow_id}/duplicate")
async def duplicate_workflow(
    request: Request, workflow_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    try:
        new_id = f"{workflow_id}-copy-{uuid.uuid4().hex[:4]}"
        duplicated = await registry.duplicate(workflow_id, new_id)
        return _wf_to_summary(duplicated)
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{workflow_id}/start")
async def start_workflow(
    request: Request, workflow_id: str, _user: dict = Depends(get_current_user)
):
    return await execute_workflow(request, workflow_id, _user)


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    request: Request, workflow_id: str, _user: dict = Depends(get_current_user)
):
    registry = _get_registry(request)
    engine = _get_engine(request)
    wf = await registry.get(workflow_id)
    if wf is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id} not found"
        )
    if engine is None:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        return {
            "id": run_id,
            "workflowId": workflow_id,
            "status": "completed",
            "startedAt": datetime.now(UTC).isoformat(),
            "completedAt": datetime.now(UTC).isoformat(),
            "duration": 0,
            "triggeredBy": "manual",
            "triggeredByType": "manual",
            "steps": [],
        }

    from eaip.workflow.models import WorkflowContext

    ctx = WorkflowContext()
    result = await engine.execute(wf, ctx)
    return {
        "id": result.run_id,
        "workflowId": workflow_id,
        "workflowName": wf.name,
        "status": result.status.value,
        "startedAt": datetime.now(UTC).isoformat(),
        "completedAt": datetime.now(UTC).isoformat(),
        "duration": result.duration_ms,
        "triggeredBy": "manual",
        "triggeredByType": "manual",
        "steps": [
            {"name": f"Step {i}", "status": "completed", "duration": 0, "nodeId": ""}
            for i in range(result.step_count or 0)
        ],
    }


@router.get("/{workflow_id}/executions")
async def list_workflow_executions(
    request: Request, workflow_id: str, _user: dict = Depends(get_current_user)
):
    engine = _get_engine(request)
    if engine is None:
        return []
    return [
        {
            "id": rid,
            "workflowId": getattr(run, "workflow_id", workflow_id),
            "workflowName": run.definition.name
            if hasattr(run, "definition") and run.definition
            else "",
            "status": run.status.value,
            "startedAt": datetime.now(UTC).isoformat(),
            "completedAt": None,
            "duration": 0,
            "triggeredBy": "manual",
            "triggeredByType": "manual",
            "steps": [],
        }
        for rid, run in engine._runs.items()
        if run.workflow_id == workflow_id
    ]


@router.get("/{workflow_id}/events")
async def list_workflow_events(
    request: Request, workflow_id: str, limit: int = 50, _user: dict = Depends(get_current_user)
):
    store = request.app.state.lifecycle.platform.container.try_resolve(EventStore)
    if store is not None:
        return store.recent_by(workflow_id=workflow_id, limit=limit)
    return []


@router.post("/executions/{execution_id}/pause")
async def pause_workflow_execution(
    request: Request, execution_id: str, _user: dict = Depends(get_current_user)
):
    engine = _get_engine(request)
    if engine:
        await engine.pause(execution_id)
    return {"status": "ok"}


@router.post("/executions/{execution_id}/resume")
async def resume_workflow_execution(
    request: Request, execution_id: str, _user: dict = Depends(get_current_user)
):
    engine = _get_engine(request)
    if engine:
        await engine.resume(execution_id)
    return {"status": "ok"}


@router.post("/executions/{execution_id}/cancel")
async def cancel_workflow_execution(
    request: Request, execution_id: str, _user: dict = Depends(get_current_user)
):
    engine = _get_engine(request)
    if engine:
        await engine.cancel(execution_id)
    return {"status": "ok"}


@router.get("/runs/{run_id}")
async def get_workflow_run(request: Request, run_id: str, _user: dict = Depends(get_current_user)):
    engine = _get_engine(request)
    if engine is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Engine not available")

    run = engine.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")

    return {
        "id": run.id,
        "workflowId": run.workflow_id,
        "workflowName": run.definition.name if run.definition else "",
        "status": run.status.value,
        "currentStep": run.steps[-1].node_id if run.steps else None,
        "startedAt": run.started_at.isoformat() if run.started_at else None,
        "completedAt": run.completed_at.isoformat() if run.completed_at else None,
        "duration": run.duration_ms,
        "triggeredBy": "manual",
        "triggeredByType": "manual",
        "steps": [
            {
                "name": s.name,
                "status": s.status.value,
                "duration": s.duration_ms,
                "nodeId": s.node_id,
            }
            for s in run.steps
        ],
    }


@router.post("/executions/{execution_id}/retry")
async def retry_workflow_execution(
    request: Request, execution_id: str, _user: dict = Depends(get_current_user)
):
    engine = _get_engine(request)
    if engine is None:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        return {
            "id": run_id,
            "workflowId": "",
            "status": "completed",
            "startedAt": datetime.now(UTC).isoformat(),
            "completedAt": datetime.now(UTC).isoformat(),
            "duration": 0,
            "triggeredBy": "manual",
            "triggeredByType": "manual",
            "steps": [],
        }

    run = engine.get_run(execution_id)
    if run is None:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        return {
            "id": run_id,
            "workflowId": "",
            "status": "completed",
            "startedAt": datetime.now(UTC).isoformat(),
            "completedAt": datetime.now(UTC).isoformat(),
            "duration": 0,
            "triggeredBy": "manual",
            "triggeredByType": "manual",
            "steps": [],
        }

    from eaip.workflow.models import WorkflowContext

    ctx = WorkflowContext(**run.context)
    result = await engine.execute(run.definition, ctx)
    return {
        "id": result.run_id,
        "workflowId": run.workflow_id,
        "workflowName": run.definition.name,
        "status": result.status.value,
        "startedAt": datetime.now(UTC).isoformat(),
        "completedAt": datetime.now(UTC).isoformat(),
        "duration": result.duration_ms,
        "triggeredBy": "manual",
        "triggeredByType": "manual",
        "steps": [
            {"name": f"Step {i}", "status": "completed", "duration": 0, "nodeId": ""}
            for i in range(result.step_count or 0)
        ],
    }
