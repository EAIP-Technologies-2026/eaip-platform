"""HTTP router for EAIP Orchestration endpoints (Phase 10).

All endpoints require authentication and flow through existing governance.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from eaip.copilot.orchestration.models import (
    CreatePlanRequest,
    PlanStatus,
)
from eaip.copilot.orchestration.service import OrchestrationService
from eaip.http.dependencies import get_current_user

router = APIRouter(
    prefix="/copilot/orchestrations", tags=["orchestrations"]
)

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def _get_service(request: Request) -> OrchestrationService:
    """Resolve the orchestration service from the container."""
    service = (
        request.app.state.lifecycle.platform.container.try_resolve(
            OrchestrationService
        )
    )
    if service is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Orchestration service unavailable",
        )
    return service


def _exc_status(exc: Exception) -> int:
    """Determine HTTP status from exception type."""
    return (
        HTTP_404_NOT_FOUND
        if isinstance(exc, ValueError)
        else HTTP_403_FORBIDDEN
    )


@router.get("")
async def list_plans(
    request: Request,
    user: CurrentUser,
    status: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List orchestration plans visible to the user."""
    service = _get_service(request)
    status_filter = None
    if status:
        try:
            status_filter = PlanStatus(status)
        except ValueError:
            pass
    try:
        plans = await service.list_plans(
            user, status=status_filter, limit=limit
        )
        return [service.serialize(p) for p in plans]
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.post("")
async def create_plan(
    request: Request,
    body: CreatePlanRequest,
    user: CurrentUser,
) -> dict[str, Any]:
    """Create a new orchestration plan."""
    service = _get_service(request)
    try:
        plan = await service.create(user, body)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.get("/{plan_id}")
async def get_plan(
    request: Request,
    plan_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Get a specific plan."""
    service = _get_service(request)
    try:
        plan = await service.get(user, plan_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    if plan is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )
    return service.serialize(plan)


@router.post("/{plan_id}/ready")
async def ready_plan(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Mark a plan as ready."""
    service = _get_service(request)
    try:
        plan = await service.ready(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/request-approval")
async def request_approval(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Request approval for a plan."""
    service = _get_service(request)
    try:
        plan = await service.request_approval(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/approve")
async def approve_plan(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Approve a plan."""
    service = _get_service(request)
    try:
        plan = await service.approve(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/execute")
async def execute_plan(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Execute an approved plan."""
    service = _get_service(request)
    try:
        plan = await service.execute(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/execute-steps")
async def execute_steps(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Execute ready steps in the plan."""
    service = _get_service(request)
    try:
        plan = await service.execute_steps(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/pause")
async def pause_plan(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Pause a running plan."""
    service = _get_service(request)
    try:
        plan = await service.pause(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/resume")
async def resume_plan(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Resume a paused plan."""
    service = _get_service(request)
    try:
        plan = await service.resume(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/cancel")
async def cancel_plan(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Cancel a plan."""
    service = _get_service(request)
    try:
        plan = await service.cancel(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.post("/{plan_id}/rollback")
async def rollback_plan(
    request: Request, plan_id: str, user: CurrentUser
) -> dict[str, Any]:
    """Rollback completed reversible steps."""
    service = _get_service(request)
    try:
        plan = await service.rollback(user, plan_id)
        return service.serialize(plan)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(
            status_code=_exc_status(exc), detail=str(exc)
        ) from exc


@router.get("/{plan_id}/timeline")
async def get_timeline(
    request: Request, plan_id: str, user: CurrentUser
) -> list[dict[str, Any]]:
    """Get the execution timeline for a plan."""
    service = _get_service(request)
    try:
        return await service.get_timeline(user, plan_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


__all__ = ["router"]
