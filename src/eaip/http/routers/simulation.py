from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger
from eaip.simulation.engine import SimulationEngine

router = APIRouter(prefix="/simulation", tags=["simulation"])
log = get_logger("eaip.http.routers.simulation")


def _get_engine(request: Request) -> SimulationEngine | None:
    return request.app.state.lifecycle.platform.container.try_resolve(SimulationEngine)


@router.get("/events")
async def list_events(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    enterprise: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    engine = _get_engine(request)
    if engine is None:
        return []
    events = engine.events
    if enterprise:
        events = [e for e in events if e.enterprise == enterprise]
    events = events[-min(limit, 200):]
    return [
        {
            "id": e.id,
            "tenant_id": e.tenant_id,
            "enterprise": e.enterprise,
            "event_type": e.event_type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.post("/tick")
async def trigger_tick(
    request: Request,
    body: dict[str, Any] | None = None,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    engine = _get_engine(request)
    if engine is None:
        engine = SimulationEngine()
    events = engine.tick()
    return {
        "tick_count": engine.tick_count,
        "events": [
            {
                "id": e.id,
                "enterprise": e.enterprise,
                "event_type": e.event_type,
                "payload": e.payload,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }


@router.get("/state/{enterprise}")
async def enterprise_state(
    request: Request,
    enterprise: str,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    engine = _get_engine(request)
    if engine is None:
        raise HTTPException(status_code=503, detail="simulation not available")
    try:
        state = engine.get_enterprise_state(enterprise)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "enterprise": state.enterprise,
        "workload": state.workload,
        "utilization": state.utilization,
        "active_tasks": state.active_tasks,
        "alerts": state.alerts,
    }


@router.get("/state")
async def all_states(
    request: Request,
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> list[dict[str, Any]]:
    engine = _get_engine(request)
    if engine is None:
        return []
    result: list[dict[str, Any]] = []
    for ent in ("apex", "nova", "meridian"):
        try:
            s = engine.get_enterprise_state(ent)
            result.append({
                "enterprise": s.enterprise,
                "workload": s.workload,
                "utilization": s.utilization,
                "active_tasks": s.active_tasks,
                "alerts": s.alerts,
            })
        except Exception:
            pass
    return result


@router.post("/generate")
async def generate_event(
    request: Request,
    body: dict[str, Any],
    user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    engine = _get_engine(request)
    if engine is None:
        engine = SimulationEngine()
    enterprise = str(body.get("enterprise", "apex"))
    event_type = str(body.get("event_type") or body.get("eventType") or "")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")
    try:
        evt = engine.generate_event(enterprise, event_type, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": evt.id,
        "tenant_id": evt.tenant_id,
        "enterprise": evt.enterprise,
        "event_type": evt.event_type,
        "payload": evt.payload,
        "created_at": evt.created_at.isoformat(),
    }
