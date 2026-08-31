from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.observability.timeline import ObservabilityEvent, get_timeline_store, new_correlation_id

router = APIRouter(prefix="/observability", tags=["observability"])


@router.post("/events", status_code=201)
async def record_event(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    store = get_timeline_store()
    # sanitize — never persist secrets
    meta = {k: v for k, v in (body.get("metadata") or {}).items() if "secret" not in k.lower() and "token" not in k.lower() and "password" not in k.lower()}
    evt = ObservabilityEvent(
        event_id=body.get("event_id") or f"evt-{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        correlation_id=str(body.get("correlation_id") or body.get("correlationId") or new_correlation_id()),
        actor=str(body.get("actor", _user.get("sub", "system") if isinstance(_user, dict) else "system")),
        resource=str(body.get("resource", "")),
        action=str(body.get("action", "")),
        status=str(body.get("status", "ok")),
        duration_ms=float(body.get("duration_ms") or 0),
        error=str(body.get("error", "")),
        metadata=meta,
    )
    store.record(evt)
    return evt.model_dump(mode="json")


@router.get("/events")
async def list_events(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), limit: int = 50) -> list[dict[str, Any]]:
    store = get_timeline_store()
    return [e.model_dump(mode="json") for e in store.list_for_tenant(tenant_id, limit=min(limit, 200))]


@router.get("/timeline/{correlation_id}")
async def get_timeline(request: Request, correlation_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    store = get_timeline_store()
    return store.reconstruct(tenant_id, correlation_id)


@router.get("/correlation/new")
async def new_correlation(request: Request, _user: dict = Depends(get_current_user)) -> dict[str, str]:
    return {"correlation_id": new_correlation_id()}
