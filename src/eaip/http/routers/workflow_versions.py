from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(prefix="/workflows/{workflow_id}/versions", tags=["workflows"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.workflow_versions")


@router.get("")
async def list_versions(request: Request, workflow_id: str):
    return []


@router.post("")
async def create_version(request: Request, workflow_id: str, body: dict[str, Any]):
    version_id = f"wfv-{uuid.uuid4().hex[:12]}"
    return {
        "id": version_id,
        "workflowId": workflow_id,
        "version": body.get("version", 1),
        "nodes": body.get("nodes", []),
        "connections": body.get("connections", []),
        "viewport": body.get("viewport", {}),
        "zoom": body.get("zoom", 1.0),
        "panX": body.get("panX", 0),
        "panY": body.get("panY", 0),
        "variables": body.get("variables", []),
        "secrets": body.get("secrets", []),
        "tags": body.get("tags", []),
        "labels": body.get("labels", []),
        "message": body.get("message", ""),
        "status": "draft",
        "createdBy": body.get("createdBy", ""),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{version_id}")
async def get_version(request: Request, workflow_id: str, version_id: str):
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Version not found")


@router.post("/{version_id}/publish")
async def publish_version(request: Request, workflow_id: str, version_id: str):
    return {"status": "published", "id": version_id}


@router.post("/{version_id}/archive")
async def archive_version(request: Request, workflow_id: str, version_id: str):
    return {"status": "archived", "id": version_id}


@router.post("/rollback")
async def rollback_to_version(request: Request, workflow_id: str, body: dict[str, Any]):
    target_version = body.get("version", 0)
    return {
        "status": "rolled_back",
        "workflowId": workflow_id,
        "targetVersion": target_version,
        "newVersionId": f"wfv-{uuid.uuid4().hex[:12]}",
    }
