"""HTTP router for EAIP Guided Tour endpoints (Phase 8).

The tour is a capability of the existing Conductor / Personal Assistant.
All endpoints require authentication and flow through the existing governance
pipeline.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from eaip.copilot.tour.fixtures import TourFixtureService
from eaip.copilot.tour.models import TourRequest, TourResponse
from eaip.copilot.tour.service import TourService
from eaip.http.dependencies import get_current_user

router = APIRouter(prefix="/tour", tags=["tour"])

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def _get_tour_service(request: Request) -> TourService:
    """Resolve the tour service from the platform container."""
    container = request.app.state.lifecycle.platform.container
    service = container.try_resolve(TourService)
    if service is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tour service unavailable")
    return service


@router.post("/start")
async def start_tour(
    request: Request,
    user: CurrentUser,
    body: dict[str, Any] | None = None,
) -> TourResponse:
    """Start a new guided platform tour for the authenticated user."""
    service = _get_tour_service(request)
    theme = "light"
    voice_enabled = False
    if body:
        theme = str(body.get("theme", "light"))
        voice_enabled = bool(body.get("voice_enabled", False))
    try:
        return await service.start_tour(user, theme=theme, voice_enabled=voice_enabled)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{tour_session_id}/command")
async def tour_command(
    request: Request,
    tour_session_id: str,
    body: TourRequest,
    user: CurrentUser,
) -> TourResponse:
    """Process a tour command (pause, resume, next, skip, etc.)."""
    service = _get_tour_service(request)
    try:
        return await service.process_command(tour_session_id, body, user)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{tour_session_id}/end")
async def end_tour(
    request: Request,
    tour_session_id: str,
    user: CurrentUser,
    body: dict[str, Any] | None = None,
) -> TourResponse:
    """End a tour session and clean up all demo fixtures."""
    service = _get_tour_service(request)
    cancelled = bool(body and body.get("cancelled", False))
    try:
        return await service.end_tour(tour_session_id, user, cancelled=cancelled)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{tour_session_id}/status")
async def tour_status(
    request: Request,
    tour_session_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """Get the current status of a tour session."""
    service = _get_tour_service(request)
    context = service.get_session(tour_session_id)
    if context is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tour session not found")
    actor = str(user.get("sub") or user.get("name") or "unknown")
    if context.user_id != actor:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Access denied")
    return {
        "tour_session_id": context.tour_session_id,
        "state": context.current_state.value,
        "current_step_index": context.current_step_index,
        "total_steps": len(context.steps),
        "current_route": context.current_route,
        "current_application": context.current_application,
        "voice_enabled": context.voice_enabled,
    }


@router.get("/preferences")
async def tour_preferences(
    request: Request,
    user: CurrentUser,
) -> dict[str, Any]:
    """Check whether the user has previously completed a tour."""
    service = _get_tour_service(request)
    completed = await service._check_tour_completed(user)
    return {"tour_completed": completed}


__all__ = ["router"]
