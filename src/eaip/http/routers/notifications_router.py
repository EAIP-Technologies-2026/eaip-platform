from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.notifications.models import NotificationCategory, NotificationSeverity

router = APIRouter(
    prefix="/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.notifications")


@router.get("")
async def list_notifications(
    request: Request,
    unread: bool = False,
    severity: str | None = None,
    category: str | None = None,
    search: str = "",
    group_key: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    user = request.state.user if hasattr(request.state, "user") else {}
    tenant_id = user.get("tenant_id", "")
    user_id = user.get("id", user.get("sub", ""))

    log.info(
        "notifications.list",
        user_id=user_id,
        tenant_id=tenant_id,
        unread=unread,
        severity=severity,
        category=category,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "notifications": [],
        "total": 0,
        "unreadCount": 0,
        "counts": {
            "total": 0,
            "unread": 0,
            "acknowledged": 0,
            "dismissed": 0,
        },
        "categoryCounts": {},
        "severityCounts": {},
    }


@router.get("/unread-count")
async def unread_count(request: Request):
    return {"count": 0}


@router.get("/counts")
async def get_counts(request: Request):
    return {
        "total": 0,
        "unread": 0,
        "acknowledged": 0,
        "dismissed": 0,
    }


@router.get("/categories")
async def get_category_counts(request: Request):
    return {cat.value: 0 for cat in NotificationCategory}


@router.get("/severities")
async def get_severity_counts(request: Request):
    return {sev.value: 0 for sev in NotificationSeverity}


@router.get("/{notification_id}")
async def get_notification(request: Request, notification_id: str):
    return {
        "id": notification_id,
        "type": "system",
        "title": "",
        "message": "",
        "summary": "",
        "severity": "info",
        "category": "system",
        "createdAt": datetime.now(UTC).isoformat(),
        "read": False,
        "acknowledged": False,
        "dismissed": False,
        "source": "",
        "deepLink": None,
        "relatedEntityId": None,
        "relatedEntityType": None,
        "groupKey": None,
    }


@router.post("/{notification_id}/read")
async def mark_read(request: Request, notification_id: str):
    return {"status": "read"}


@router.post("/read")
async def mark_read_batch(request: Request, body: dict[str, Any]):
    ids = body.get("ids", [])
    return {"status": "read", "count": len(ids)}


@router.post("/read-all")
async def mark_all_read(request: Request):
    return {"status": "all_read", "count": 0}


@router.post("/{notification_id}/acknowledge")
async def acknowledge_notification(request: Request, notification_id: str):
    return {"status": "acknowledged"}


@router.post("/{notification_id}/dismiss")
async def dismiss_notification(request: Request, notification_id: str):
    return {"status": "dismissed"}


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
        "summary": body.get("summary", ""),
        "severity": body.get("severity", "info"),
        "category": body.get("category", "system"),
        "createdAt": datetime.now(UTC).isoformat(),
        "read": False,
        "acknowledged": False,
        "dismissed": False,
        "source": body.get("source", ""),
        "deepLink": body.get("deepLink"),
        "relatedEntityId": body.get("relatedEntityId"),
        "relatedEntityType": body.get("relatedEntityType"),
        "groupKey": body.get("groupKey"),
    }
