from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger
from eaip.scheduling.exceptions import ScheduleNotFoundError, ScheduleValidationError
from eaip.scheduling.models import (
    ExecutionWindow,
    RetryPolicy,
    ScheduleDefinition,
    ScheduleKind,
    ScheduleStatus,
    ScheduleTargetType,
    ScheduleTrigger,
)
from eaip.scheduling.repository import ScheduleExecutionRepository, ScheduleRepository
from eaip.scheduling.service import SchedulingService

router = APIRouter(prefix="/schedules", tags=["scheduling"])
log = get_logger("eaip.http.routers.scheduling")


def _get_service(request: Request) -> SchedulingService:
    svc = request.app.state.lifecycle.platform.container.try_resolve(SchedulingService)
    if svc is not None:
        return svc
    repo = request.app.state.lifecycle.platform.container.try_resolve(ScheduleRepository)
    exec_repo = request.app.state.lifecycle.platform.container.try_resolve(ScheduleExecutionRepository)
    if repo is not None:
        return SchedulingService(repo=repo, exec_repo=exec_repo)
    return SchedulingService()


def _def_to_dict(defn: ScheduleDefinition) -> dict[str, Any]:
    return {
        "id": defn.id,
        "tenant_id": defn.tenant_id,
        "name": defn.name,
        "description": defn.description,
        "target_type": defn.target_type.value,
        "target_id": defn.target_id,
        "trigger": {
            "kind": defn.trigger.kind.value,
            "cron_expr": defn.trigger.cron_expr,
            "interval_seconds": defn.trigger.interval_seconds,
            "run_at": defn.trigger.run_at.isoformat() if defn.trigger.run_at else None,
            "timezone": defn.trigger.timezone,
        },
        "execution_window": {
            "start_window": defn.execution_window.start_window if defn.execution_window else None,
            "end_window": defn.execution_window.end_window if defn.execution_window else None,
            "calendar_days": list(defn.execution_window.calendar_days) if defn.execution_window and defn.execution_window.calendar_days else None,
        } if defn.execution_window else None,
        "priority": defn.priority,
        "dependencies": list(defn.dependencies),
        "retry_policy": {
            "max_retries": defn.retry_policy.max_retries,
            "delay_seconds": defn.retry_policy.delay_seconds,
            "backoff_multiplier": defn.retry_policy.backoff_multiplier,
        },
        "status": defn.status.value,
        "created_by": defn.created_by,
        "created_at": defn.created_at.isoformat(),
        "updated_at": defn.updated_at.isoformat(),
        "next_run_at": defn.next_run_at.isoformat() if defn.next_run_at else None,
        "last_run_at": defn.last_run_at.isoformat() if defn.last_run_at else None,
        "metadata": defn.metadata,
    }


@router.post("")
async def create_schedule(
    request: Request,
    body: dict[str, Any],
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    trigger_raw = body.get("trigger") or {}
    if isinstance(trigger_raw, dict) and "kind" not in trigger_raw:
        if trigger_raw.get("cron_expr"):
            trigger_raw["kind"] = "cron"
        elif trigger_raw.get("interval_seconds"):
            trigger_raw["kind"] = "interval"
        elif trigger_raw.get("run_at"):
            trigger_raw["kind"] = "one_time"
        else:
            trigger_raw["kind"] = "one_time"
    try:
        trigger = ScheduleTrigger.model_validate(trigger_raw) if trigger_raw else ScheduleTrigger(kind=ScheduleKind.ONE_TIME)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    target_type_raw = body.get("target_type") or body.get("targetType") or "workflow"
    try:
        target_type = ScheduleTargetType(target_type_raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid target_type {target_type_raw!r}") from exc
    window = None
    if body.get("execution_window") or body.get("executionWindow"):
        w_raw = body.get("execution_window") or body.get("executionWindow") or {}
        try:
            window = ExecutionWindow.model_validate(w_raw)
        except Exception:
            window = None
    retry = None
    if body.get("retry_policy") or body.get("retryPolicy"):
        r_raw = body.get("retry_policy") or body.get("retryPolicy") or {}
        try:
            retry = RetryPolicy.model_validate(r_raw)
        except Exception:
            retry = RetryPolicy()
    if retry is None:
        retry = RetryPolicy()
    definition = ScheduleDefinition(
        id=body.get("id") or f"sched-{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        name=body.get("name", "Unnamed Schedule"),
        description=body.get("description", ""),
        target_type=target_type,
        target_id=str(body.get("target_id") or body.get("targetId") or ""),
        trigger=trigger,
        execution_window=window,
        priority=int(body.get("priority", 1)),
        dependencies=tuple(body.get("dependencies", [])),
        retry_policy=retry,
        status=ScheduleStatus.ACTIVE,
        created_by=str(user.get("sub") or user.get("id") or ""),
        metadata=body.get("metadata") or {},
    )
    try:
        created = await svc.create_schedule(definition)
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log.info("schedule.created", schedule_id=created.id, tenant_id=tenant_id)
    return _def_to_dict(created)


@router.get("")
async def list_schedules(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    status: str | None = None,
    kind: str | None = None,
    priority: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    svc = _get_service(request)
    results = await svc.list_schedules(tenant_id, status=status, kind=kind, priority=priority, limit=min(limit, 200))
    return [_def_to_dict(r) for r in results]


@router.get("/stats")
async def schedule_stats(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    return await svc.get_stats(tenant_id)


@router.get("/upcoming")
async def upcoming_schedules(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    horizon_hours: int = 24,
) -> list[dict[str, Any]]:
    svc = _get_service(request)
    results = await svc.get_upcoming(tenant_id, horizon_hours=min(horizon_hours, 168))
    return [_def_to_dict(r) for r in results]


@router.get("/{schedule_id}")
async def get_schedule(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    try:
        found = await svc.get_schedule(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _def_to_dict(found)


@router.put("/{schedule_id}")
async def update_schedule(
    request: Request,
    schedule_id: str,
    body: dict[str, Any],
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    allowed = {"name", "description", "priority", "trigger", "execution_window", "executionWindow", "retry_policy", "retryPolicy", "dependencies", "metadata"}
    updates: dict[str, Any] = {k: v for k, v in body.items() if k in allowed}
    if "executionWindow" in updates and "execution_window" not in updates:
        updates["execution_window"] = updates.pop("executionWindow")
    if "retryPolicy" in updates and "retry_policy" not in updates:
        updates["retry_policy"] = updates.pop("retryPolicy")
    try:
        updated = await svc.update_schedule(schedule_id, tenant_id, updates)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _def_to_dict(updated)


@router.delete("/{schedule_id}")
async def delete_schedule(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    try:
        await svc.get_schedule(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    repo = svc._repo
    ok = await repo.delete(schedule_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="schedule not found")
    return {"status": "deleted", "id": schedule_id}


@router.post("/{schedule_id}/pause")
async def pause_schedule(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    try:
        result = await svc.pause(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _def_to_dict(result)


@router.post("/{schedule_id}/resume")
async def resume_schedule(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    try:
        result = await svc.resume(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _def_to_dict(result)


@router.post("/{schedule_id}/cancel")
async def cancel_schedule(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    try:
        result = await svc.cancel(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _def_to_dict(result)


@router.post("/{schedule_id}/reschedule")
async def reschedule_schedule(
    request: Request,
    schedule_id: str,
    body: dict[str, Any],
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    trigger_raw = body.get("trigger") or body
    try:
        result = await svc.reschedule(schedule_id, tenant_id, trigger_raw)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _def_to_dict(result)


@router.post("/{schedule_id}/execute")
async def execute_schedule(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    try:
        execution = await svc.execute(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": execution.id,
        "schedule_id": execution.schedule_id,
        "tenant_id": execution.tenant_id,
        "status": execution.status,
        "attempt": execution.attempt,
        "scheduled_at": execution.scheduled_at.isoformat(),
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "result": execution.result,
        "error": execution.error,
    }


@router.get("/{schedule_id}/executions")
async def list_executions(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    limit: int = 50,
) -> list[dict[str, Any]]:
    svc = _get_service(request)
    try:
        await svc.get_schedule(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    execs = await svc._exec_repo.list_by_schedule(schedule_id, tenant_id, limit=min(limit, 200))
    return [
        {
            "id": e.id,
            "schedule_id": e.schedule_id,
            "tenant_id": e.tenant_id,
            "status": e.status,
            "attempt": e.attempt,
            "scheduled_at": e.scheduled_at.isoformat(),
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "result": e.result,
            "error": e.error,
        }
        for e in execs
    ]


@router.get("/{schedule_id}/health")
async def schedule_health(
    request: Request,
    schedule_id: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    svc = _get_service(request)
    try:
        health = await svc.get_health(schedule_id, tenant_id)
    except ScheduleNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {
        "schedule_id": health.schedule_id,
        "health_score": health.health_score,
        "failure_rate": health.failure_rate,
        "overdue_count": health.overdue_count,
        "total_executions": health.total_executions,
        "failed_executions": health.failed_executions,
    }
