from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(prefix="/marketplace", tags=["marketplace"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.marketplace")


@router.get("/packages")
async def list_packages(request: Request, search: str = "", category: str = "", page: int = 1, pageSize: int = 20):
    return {"packages": [], "total": 0, "page": page, "pageSize": pageSize}


@router.get("/packages/featured")
async def featured_packages(request: Request):
    return {"packages": []}


@router.get("/packages/{package_id}")
async def get_package(request: Request, package_id: str):
    return {
        "id": package_id,
        "name": f"Package {package_id}",
        "description": "Enterprise package",
        "type": "template",
        "version": "1.0.0",
        "author": "EAIP",
        "downloads": 0,
        "rating": 4.5,
        "tags": [],
        "status": "published",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/packages")
async def create_package(request: Request, body: dict[str, Any]):
    return {
        "id": f"pkg-{uuid.uuid4().hex[:8]}",
        "name": body.get("name", ""),
        "status": "draft",
    }


@router.get("/installations")
async def list_installations(request: Request):
    return []


@router.post("/packages/{package_id}/install")
async def install_package(request: Request, package_id: str):
    return {"status": "installed", "id": f"inst-{uuid.uuid4().hex[:8]}"}


@router.post("/packages/{package_id}/uninstall")
async def uninstall_package(request: Request, package_id: str):
    return {"status": "uninstalled"}


@router.get("/categories")
async def list_categories(request: Request):
    return {
        "categories": [
            {"id": "agent-packs", "name": "Agent Packs", "count": 0},
            {"id": "workflow-packs", "name": "Workflow Packs", "count": 0},
            {"id": "knowledge-packs", "name": "Knowledge Packs", "count": 0},
            {"id": "templates", "name": "Templates", "count": 0},
            {"id": "deployment-packs", "name": "Deployment Packs", "count": 0},
            {"id": "industry-packs", "name": "Industry Packs", "count": 0},
        ]
    }
