from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(
    prefix="/organizations", tags=["organizations"], dependencies=[Depends(get_current_user)]
)
log = get_logger("eaip.http.routers.organizations")


@router.get("")
async def list_organizations(request: Request):
    return []


@router.post("")
async def create_organization(request: Request, body: dict[str, Any]):
    return {
        "id": body.get("id", f"org-{uuid.uuid4().hex[:8]}"),
        "name": body.get("name", "New Organization"),
        "slug": body.get("slug", ""),
        "memberCount": 0,
    }


@router.get("/{org_id}")
async def get_organization(request: Request, org_id: str):
    return {
        "id": org_id,
        "name": "Default Organization",
        "slug": "default",
        "memberCount": 0,
    }
