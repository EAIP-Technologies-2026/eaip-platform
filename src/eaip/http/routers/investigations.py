"""HTTP router for EAIP Investigation endpoints (Phase 9).

Investigations are persistent, governed analytical sessions.  All endpoints
require authentication and flow through the existing governance pipeline.
"""

from __future__ import annotations

import contextlib
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from eaip.copilot.investigation.models import (
    CreateInvestigationRequest,
    InvestigationStatus,
)
from eaip.copilot.investigation.service import InvestigationService
from eaip.http.dependencies import get_current_user

router = APIRouter(
    prefix="/copilot/investigations", tags=["investigations"]
)

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def _get_service(request: Request) -> InvestigationService:
    """Resolve the investigation service from the container."""
    service = request.app.state.lifecycle.platform.container.try_resolve(
        InvestigationService
    )
    if service is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Investigation service unavailable",
        )
    return service


@router.get("")
async def list_investigations(
    request: Request,
    user: CurrentUser,
    status: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List investigations visible to the authenticated user."""
    service = _get_service(request)
    status_filter = None
    if status:
        with contextlib.suppress(ValueError):
            status_filter = InvestigationStatus(status)
    try:
        investigations = await service.list_investigations(
            user, status=status_filter, limit=limit
        )
        return [service.serialize(i) for i in investigations]
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.post("")
async def create_investigation(
    request: Request,
    body: CreateInvestigationRequest,
    user: CurrentUser,
) -> dict[str, Any]:
    """Create a new investigation."""
    service = _get_service(request)
    try:
        inv = await service.create(user, body)
        return service.serialize(inv)
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get("/resumable")
async def find_resumable(
    request: Request,
    user: CurrentUser,
    q: str = "",
) -> dict[str, Any] | None:
    """Find the most recent resumable investigation."""
    service = _get_service(request)
    try:
        inv = await service.find_resumable(user, q)
        if inv is None:
            return None
        return service.serialize(inv)
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get("/{investigation_id}")
async def get_investigation(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Get a specific investigation."""
    service = _get_service(request)
    try:
        inv = await service.get(user, investigation_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    if inv is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Investigation not found",
        )
    return service.serialize(inv)


@router.post("/{investigation_id}/start")
async def start_investigation(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Start a draft investigation."""
    service = _get_service(request)
    try:
        inv = await service.start(user, investigation_id)
        return service.serialize(inv)
    except (ValueError, PermissionError) as exc:
        status = (
            HTTP_404_NOT_FOUND
            if isinstance(exc, ValueError)
            else HTTP_403_FORBIDDEN
        )
        raise HTTPException(
            status_code=status, detail=str(exc)
        ) from exc


@router.post("/{investigation_id}/pause")
async def pause_investigation(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Pause an active investigation."""
    service = _get_service(request)
    try:
        inv = await service.pause(user, investigation_id)
        return service.serialize(inv)
    except (ValueError, PermissionError) as exc:
        status = (
            HTTP_404_NOT_FOUND
            if isinstance(exc, ValueError)
            else HTTP_403_FORBIDDEN
        )
        raise HTTPException(
            status_code=status, detail=str(exc)
        ) from exc


@router.post("/{investigation_id}/resume")
async def resume_investigation(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Resume a paused investigation."""
    service = _get_service(request)
    try:
        inv = await service.resume(user, investigation_id)
        return service.serialize(inv)
    except (ValueError, PermissionError) as exc:
        status = (
            HTTP_404_NOT_FOUND
            if isinstance(exc, ValueError)
            else HTTP_403_FORBIDDEN
        )
        raise HTTPException(
            status_code=status, detail=str(exc)
        ) from exc


@router.post("/{investigation_id}/resolve")
async def resolve_investigation(
    request: Request,
    investigation_id: str,
    body: dict[str, Any],
    user: CurrentUser,
) -> dict[str, Any]:
    """Resolve an investigation with findings."""
    service = _get_service(request)
    summary = str(body.get("summary", ""))
    findings = tuple(
        str(f) for f in body.get("findings", []) if isinstance(f, str)
    )
    recommendations = tuple(
        str(r)
        for r in body.get("recommendations", [])
        if isinstance(r, str)
    )
    try:
        inv = await service.resolve(
            user,
            investigation_id,
            summary=summary,
            findings=findings,
            recommendations=recommendations,
        )
        return service.serialize(inv)
    except (ValueError, PermissionError) as exc:
        status = (
            HTTP_404_NOT_FOUND
            if isinstance(exc, ValueError)
            else HTTP_403_FORBIDDEN
        )
        raise HTTPException(
            status_code=status, detail=str(exc)
        ) from exc


@router.post("/{investigation_id}/archive")
async def archive_investigation(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Archive a resolved investigation."""
    service = _get_service(request)
    try:
        inv = await service.archive(user, investigation_id)
        return service.serialize(inv)
    except (ValueError, PermissionError) as exc:
        status = (
            HTTP_404_NOT_FOUND
            if isinstance(exc, ValueError)
            else HTTP_403_FORBIDDEN
        )
        raise HTTPException(
            status_code=status, detail=str(exc)
        ) from exc


@router.post("/{investigation_id}/cancel")
async def cancel_investigation(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Cancel an investigation."""
    service = _get_service(request)
    try:
        inv = await service.cancel(user, investigation_id)
        return service.serialize(inv)
    except (ValueError, PermissionError) as exc:
        status = (
            HTTP_404_NOT_FOUND
            if isinstance(exc, ValueError)
            else HTTP_403_FORBIDDEN
        )
        raise HTTPException(
            status_code=status, detail=str(exc)
        ) from exc


@router.delete("/{investigation_id}")
async def delete_investigation(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Delete an investigation."""
    service = _get_service(request)
    try:
        deleted = await service.delete(user, investigation_id)
        if not deleted:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Investigation not found",
            )
        return {"status": "deleted", "id": investigation_id}
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get("/{investigation_id}/timeline")
async def get_timeline(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    """Get the investigation timeline."""
    service = _get_service(request)
    try:
        events = await service.get_timeline(user, investigation_id)
        return [service.serialize_timeline(e) for e in events]
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get("/{investigation_id}/evidence")
async def get_evidence(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    """Get evidence for an investigation."""
    service = _get_service(request)
    try:
        evidence = await service.get_evidence(
            user, investigation_id
        )
        return [service.serialize_evidence(e) for e in evidence]
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get("/{investigation_id}/hypotheses")
async def get_hypotheses(
    request: Request,
    investigation_id: str,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    """Get hypotheses for an investigation."""
    service = _get_service(request)
    try:
        hypotheses = await service.get_hypotheses(
            user, investigation_id
        )
        return [
            {
                "id": h.id,
                "investigation_id": h.investigation_id,
                "statement": h.statement,
                "confidence": h.confidence,
                "supporting_evidence_ids": list(
                    h.supporting_evidence_ids
                ),
                "contradicting_evidence_ids": list(
                    h.contradicting_evidence_ids
                ),
                "status": h.status,
                "created_at": h.created_at.isoformat(),
                "updated_at": h.updated_at.isoformat(),
            }
            for h in hypotheses
        ]
    except PermissionError as exc:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


__all__ = ["router"]
