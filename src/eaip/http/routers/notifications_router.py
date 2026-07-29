from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(prefix="/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.notifications")


@router.get("")
async def list_notifications(request: Request, unread: bool = False, limit: int = 50, offset: int = 0):
    return {"notifications": [], "total": 0, "unreadCount": 0}


@router.get("/unread-count")
async def unread_count(request: Request):
    return {"count": 0}


@router.post("/{notification_id}/read")
async def mark_read(request: Request, notification_id: str):
    return {"status": "read"}


@router.post("/read-all")
async def mark_all_read(request: Request):
    return {"status": "all_read", "count": 0}


@router.delete("/{notification_id}")
async def delete_notification(request: Request, notification_id: str):
    return {"status": "deleted"}


@router.post("")
async def create_notification(request: Request, body: dict[str, Any]):
    return {
        "id": f"notif-{uuid.uuid4().hex[:12]}",
        "type": body.get("type", "info"),
        "title": body.get("title", ""),
        "message": body.get("message", ""),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }
