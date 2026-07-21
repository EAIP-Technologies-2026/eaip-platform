from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.logging.context import get_logger
from eaip.organization.service import OrganizationService

router = APIRouter(prefix="/admin", tags=["admin"])
log = get_logger("eaip.http.routers.admin")


def _get_org_service(request: Request) -> OrganizationService | None:
    return request.app.state.lifecycle.platform.container.try_resolve(OrganizationService)


@router.get("/snapshot")
async def admin_snapshot(request: Request):
    container = request.app.state.lifecycle.platform.container
    services = []
    for key in container.keys():
        key_str = str(key)
        if key_str.startswith("<class 'eaip."):
            name = key_str.split(".")[-1].rstrip("'>")
            try:
                inst = container.try_resolve(key)
                services.append({"name": name, "status": "healthy" if inst is not None else "unhealthy"})
            except Exception:
                services.append({"name": name, "status": "unknown"})
    return {
        "services": services[:100],
        "health": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/users")
async def admin_users(request: Request, search: str = "", page: int = 1, pageSize: int = 20):
    return {"users": [], "total": 0, "page": page, "pageSize": pageSize}


@router.post("/users")
async def create_admin_user(request: Request, body: dict[str, Any]):
    return {"id": f"user-{uuid.uuid4().hex[:8]}", "name": body.get("name", ""), "email": body.get("email", ""), "status": "active"}


@router.get("/users/{user_id}")
async def get_admin_user(request: Request, user_id: str):
    return {"id": user_id, "name": "User", "email": "user@example.com", "roles": ["user"], "status": "active", "createdAt": datetime.now(timezone.utc).isoformat()}


@router.put("/users/{user_id}")
async def update_admin_user(request: Request, user_id: str, body: dict[str, Any]):
    return {"id": user_id, "name": body.get("name", ""), "email": body.get("email", "")}


@router.delete("/users/{user_id}")
async def delete_admin_user(request: Request, user_id: str):
    return {"status": "deleted"}


@router.post("/users/{user_id}/suspend")
async def suspend_user(request: Request, user_id: str):
    return {"status": "suspended"}


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(request: Request, user_id: str):
    return {"status": "reactivated"}


@router.get("/roles")
async def list_roles(request: Request):
    return {"roles": [
        {"id": "admin", "name": "Administrator", "description": "Full platform access", "permissionCount": 50, "memberCount": 1},
        {"id": "operator", "name": "Operator", "description": "Operational access", "permissionCount": 30, "memberCount": 3},
        {"id": "viewer", "name": "Viewer", "description": "Read-only access", "permissionCount": 10, "memberCount": 5},
    ]}


@router.post("/roles")
async def create_role(request: Request, body: dict[str, Any]):
    return {"id": f"role-{uuid.uuid4().hex[:8]}", "name": body.get("name", ""), "description": body.get("description", "")}


@router.get("/settings")
async def get_settings(request: Request):
    platform = request.app.state.lifecycle.platform
    settings = platform.settings
    return {
        "general": {"appName": settings.core.app_name, "environment": settings.core.environment.value},
            "logging": {"level": settings.logging.level, "format": settings.logging.format},
        "telemetry": {"serviceName": settings.telemetry.service_name, "endpoint": settings.telemetry.otlp_endpoint},
    }


@router.put("/settings")
async def update_settings(request: Request, body: dict[str, Any]):
    return {"status": "updated"}


@router.get("/deployments")
async def admin_deployments(request: Request):
    return []


@router.get("/audit")
async def admin_audit_logs(
    request: Request,
    action: str = "",
    actor: str = "",
    resource: str = "",
    page: int = 1,
    pageSize: int = 50,
):
    return {"entries": [], "total": 0, "page": page, "pageSize": pageSize}


@router.get("/licenses")
async def list_licenses(request: Request):
    return []


@router.post("/licenses")
async def create_license(request: Request, body: dict[str, Any]):
    return {"id": f"lic-{uuid.uuid4().hex[:8]}", "name": body.get("name", ""), "status": "active"}


@router.get("/feature-flags")
async def list_feature_flags(request: Request):
    registry = request.app.state.lifecycle.platform.feature_flags
    return {"flags": [{"name": f, "enabled": True} for f in registry._flags] if hasattr(registry, "_flags") else []}


@router.post("/feature-flags/{flag_name}/toggle")
async def toggle_feature_flag(request: Request, flag_name: str):
    return {"name": flag_name, "enabled": True}
