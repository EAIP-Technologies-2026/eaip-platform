from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.workforce.models import WorkerDefinition, WorkerType

router = APIRouter(prefix="/workforce", tags=["workforce"])
log = get_logger("eaip.http.routers.workforce")


def _get_registry(request: Request):
    return request.app.state.lifecycle.platform.container.try_resolve("WorkerRegistry")


def _get_orchestrator(request: Request):
    return request.app.state.lifecycle.platform.container.try_resolve("WorkforceOrchestrator")


def _worker_to_dict(w: WorkerDefinition) -> dict[str, Any]:
    return {
        "id": w.id,
        "name": w.name,
        "workerType": w.worker_type.value,
        "agentId": w.agent_id,
        "workflowId": w.workflow_id,
        "description": w.description,
        "tags": list(w.tags),
        "maxConcurrentRuns": w.max_concurrent_runs,
        "timeoutSeconds": w.timeout_seconds,
    }


@router.get("/workers")
async def list_workers(
    request: Request,
    worker_type: str | None = None,
    _user: dict = Depends(get_current_user),
):
    registry = _get_registry(request)
    if not registry:
        return []
    wt = WorkerType(worker_type) if worker_type else None
    return [_worker_to_dict(w) for w in registry.list_workers(worker_type=wt)]


@router.post("/workers", status_code=201)
async def register_worker(
    request: Request,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    registry = _get_registry(request)
    if not registry:
        raise HTTPException(status_code=503, detail="workforce not available")
    definition = WorkerDefinition(
        id=body.get("id", f"worker-{uuid.uuid4().hex[:8]}"),
        name=body.get("name", "Unnamed Worker"),
        worker_type=WorkerType(body.get("workerType", "agent")),
        agent_id=body.get("agentId", ""),
        workflow_id=body.get("workflowId", ""),
        description=body.get("description", ""),
        tags=tuple(body.get("tags", [])),
        max_concurrent_runs=body.get("maxConcurrentRuns", 1),
        timeout_seconds=body.get("timeoutSeconds", 0.0),
    )
    registered = registry.register_worker(definition)
    return _worker_to_dict(registered)


@router.get("/workers/{worker_id}")
async def get_worker(
    request: Request,
    worker_id: str,
    _user: dict = Depends(get_current_user),
):
    registry = _get_registry(request)
    if not registry:
        raise HTTPException(status_code=503, detail="workforce not available")
    try:
        worker = registry.get_worker(worker_id)
        return _worker_to_dict(worker)
    except Exception:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Worker {worker_id} not found")


@router.delete("/workers/{worker_id}")
async def unregister_worker(
    request: Request,
    worker_id: str,
    _user: dict = Depends(get_current_user),
):
    registry = _get_registry(request)
    if not registry:
        raise HTTPException(status_code=503, detail="workforce not available")
    try:
        registry.unregister_worker(worker_id)
        return {"status": "deleted"}
    except Exception:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Worker {worker_id} not found")


@router.post("/assignments")
async def assign_task(
    request: Request,
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
):
    orchestrator = _get_orchestrator(request)
    if not orchestrator:
        raise HTTPException(status_code=503, detail="workforce not available")

    worker_id = body.get("workerId", "")
    task = body.get("task", "")
    if not worker_id or not task:
        raise HTTPException(status_code=400, detail="workerId and task are required")

    assignment = await orchestrator.assign(worker_id, task)
    executed = await orchestrator.execute_assignment(assignment)
    return {
        "id": executed.id,
        "workerId": executed.worker_id,
        "status": executed.status.value,
        "result": executed.result,
        "error": executed.error,
    }


@router.get("/assignments")
async def list_assignments(
    request: Request,
    worker_id: str | None = None,
    _user: dict = Depends(get_current_user),
):
    orchestrator = _get_orchestrator(request)
    if not orchestrator:
        return []
    assignments = orchestrator.list_assignments(worker_id=worker_id)
    return [
        {
            "id": a.id,
            "workerId": a.worker_id,
            "taskDescription": a.task_description,
            "status": a.status.value,
            "result": a.result,
            "error": a.error,
        }
        for a in assignments
    ]


@router.get("/metrics")
async def workforce_metrics(
    request: Request,
    _user: dict = Depends(get_current_user),
):
    orchestrator = _get_orchestrator(request)
    if not orchestrator:
        return {}
    m = orchestrator.get_metrics()
    return {
        "totalAssignments": m.total_assignments,
        "activeAssignments": m.active_assignments,
        "completedAssignments": m.completed_assignments,
        "failedAssignments": m.failed_assignments,
        "avgDurationMs": m.avg_duration_ms,
        "workersRegistered": m.workers_registered,
    }
