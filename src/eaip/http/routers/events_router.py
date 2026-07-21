from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from eaip.events.event import DomainEvent
from eaip.logging.context import get_logger

router = APIRouter(prefix="/events", tags=["events"])
log = get_logger("eaip.http.routers.events")


class GenericEvent(DomainEvent):
    model_config = {"frozen": True, "extra": "allow"}


@router.get("/activity")
async def list_activity(request: Request, limit: int = 50):
    return []


@router.get("")
async def list_events(request: Request, limit: int = 50):
    return []


@router.post("/subscribe")
async def subscribe_to_event(request: Request, body: dict[str, Any]):
    return {"subscriptionId": "sub-" + body.get("type", "unknown")}


@router.post("/publish")
async def publish_event(request: Request, body: dict[str, Any]):
    lifecycle = request.app.state.lifecycle
    payload = body.get("payload", {})
    try:
        event = GenericEvent(**payload) if isinstance(payload, dict) else GenericEvent()
        await lifecycle.platform.events.publish(event)
    except Exception as e:
        log.warning("event.publish_failed", error=str(e))
    return {"eventId": "evt-published"}
