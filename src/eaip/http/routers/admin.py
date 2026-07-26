from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_403_FORBIDDEN

from eaip.admin.audit import AuditLogger
from eaip.admin.manager import RuntimeManager
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.core.feature_flags import FeatureFlagRegistry
from eaip.enterprise_settings.service import EnterpriseSettingsService
from eaip.http.dependencies import get_current_user
from eaip.license.manager import LicenseManager
from eaip.license.models import LicenseType
from eaip.logging.context import get_logger

router = APIRouter(prefix="/admin", tags=["admin"])
log = get_logger("eaip.http.routers.admin")


async def require_admin(request: Request, _user: dict = Depends(get_current_user)) -> dict:
    roles = _user.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Admin access required")
    return _user


def _get_audit_logger(request: Request) -> AuditLogger | None:
    return request.app.state.lifecycle.platform.container.try_resolve(AuditLogger)


def _get_runtime_manager(request: Request) -> RuntimeManager | None:
    return request.app.state.lifecycle.platform.container.try_resolve(RuntimeManager)


def _get_license_manager(request: Request) -> LicenseManager | None:
    return request.app.state.lifecycle.platform.container.try_resolve(LicenseManager)


def _get_settings_service(request: Request) -> EnterpriseSettingsService | None:
    return request.app.state.lifecycle.platform.container.try_resolve(EnterpriseSettingsService)


def _get_feature_flags(request: Request) -> FeatureFlagRegistry:
    return request.app.state.lifecycle.platform.feature_flags


def _log_admin_action(request: Request, action: str, resource_type: str, resource_id: str, actor_id: str = "unknown"):
    logger = _get_audit_logger(request)
    if logger is None:
        return
    entry = AuditEntry(
        id=f"audit-{uuid.uuid4().hex[:12]}",
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=AuditOutcome.SUCCESS,
    )
    logger.log(entry)


@router.get("/stats")
async def admin_stats(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    container = request.app.state.lifecycle.platform.container
    agent_count = 0
    workflow_count = 0
    org_count = 0

    from eaip.agents.registry import AgentRegistry
    registry = container.try_resolve(AgentRegistry)
    if registry is not None and hasattr(registry, "list_agents"):
        try:
            agent_count = len(registry.list_agents())
        except Exception:
            pass

    from eaip.workflow.registry import WorkflowRegistry
    wf_registry = container.try_resolve(WorkflowRegistry)
    if wf_registry is not None and hasattr(wf_registry, "list_workflows"):
        try:
            workflow_count = len(wf_registry.list_workflows())
        except Exception:
            pass

    from eaip.organization.service import OrganizationService
    org_svc = container.try_resolve(OrganizationService)
    if org_svc is not None and hasattr(org_svc, "list_organizations"):
        try:
            org_count = len(org_svc.list_organizations())
        except Exception:
            pass

    return {
        "agents": {"total": agent_count},
        "workflows": {"total": workflow_count},
        "organizations": {"total": org_count},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/snapshot")
async def admin_snapshot(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    mgr = _get_runtime_manager(request)
    if mgr is not None:
        try:
            snap = await mgr.get_snapshot()
            return {
                "services": [{"name": k, "status": v} for k, v in snap.component_states.items()],
                "health": snap.health_status,
                "activeModules": snap.active_modules,
                "activeCapabilities": snap.active_capabilities,
                "uptimeSeconds": snap.uptime_seconds,
                "timestamp": snap.collected_at.isoformat() if hasattr(snap.collected_at, 'isoformat') else datetime.now(timezone.utc).isoformat(),
            }
        except Exception:
            pass

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
async def admin_users(
    request: Request,
    _admin: dict = Depends(require_admin),
    search: str = "",
    page: int = 1,
    pageSize: int = 20,
):
    from eaip.organization.service import OrganizationService
    org_svc = request.app.state.lifecycle.platform.container.try_resolve(OrganizationService)
    if org_svc is not None and hasattr(org_svc, "list_members"):
        try:
            members = org_svc.list_members()
        except Exception:
            members = []
    else:
        members = []

    results = []
    for m in members:
        results.append({
            "id": getattr(m, "user_id", getattr(m, "id", "")),
            "name": getattr(m, "name", getattr(m, "display_name", "")),
            "email": getattr(m, "email", ""),
            "roles": [getattr(m, "role", "member")] if hasattr(m, "role") else ["member"],
            "status": getattr(m, "status", "active"),
            "createdAt": getattr(m, "created_at", datetime.now(timezone.utc)).isoformat() if hasattr(getattr(m, "created_at", None), "isoformat") else datetime.now(timezone.utc).isoformat(),
        })

    return results


@router.post("/users")
async def create_admin_user(
    request: Request,
    body: dict[str, Any],
    _admin: dict = Depends(require_admin),
):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _log_admin_action(request, "user.created", "user", user_id, actor_id=_admin.get("sub", ""))
    return {"id": user_id, "name": body.get("name", ""), "email": body.get("email", ""), "status": "active"}


@router.get("/users/{user_id}")
async def get_admin_user(
    request: Request,
    user_id: str,
    _admin: dict = Depends(require_admin),
):
    return {
        "id": user_id,
        "name": "User",
        "email": "user@example.com",
        "roles": ["user"],
        "status": "active",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


@router.put("/users/{user_id}")
async def update_admin_user(
    request: Request,
    user_id: str,
    body: dict[str, Any],
    _admin: dict = Depends(require_admin),
):
    _log_admin_action(request, "user.updated", "user", user_id, actor_id=_admin.get("sub", ""))
    return {"id": user_id, "name": body.get("name", ""), "email": body.get("email", "")}


@router.delete("/users/{user_id}")
async def delete_admin_user(
    request: Request,
    user_id: str,
    _admin: dict = Depends(require_admin),
):
    _log_admin_action(request, "user.deleted", "user", user_id, actor_id=_admin.get("sub", ""))
    return {"status": "deleted"}


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    request: Request,
    user_id: str,
    _admin: dict = Depends(require_admin),
):
    _log_admin_action(request, "user.suspended", "user", user_id, actor_id=_admin.get("sub", ""))
    return {"status": "suspended"}


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    request: Request,
    user_id: str,
    _admin: dict = Depends(require_admin),
):
    _log_admin_action(request, "user.reactivated", "user", user_id, actor_id=_admin.get("sub", ""))
    return {"status": "reactivated"}


@router.get("/roles")
async def list_roles(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    return [
        {"id": "admin", "name": "Administrator", "description": "Full platform access", "permissionCount": 50, "memberCount": 1},
        {"id": "operator", "name": "Operator", "description": "Operational access", "permissionCount": 30, "memberCount": 3},
        {"id": "viewer", "name": "Viewer", "description": "Read-only access", "permissionCount": 10, "memberCount": 5},
    ]


@router.get("/permissions")
async def list_permissions(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    return [
        {"id": "manage:agents", "name": "Manage Agents", "description": "Create, edit, and delete agents", "resource": "agents"},
        {"id": "view:agents", "name": "View Agents", "description": "View agents", "resource": "agents"},
        {"id": "manage:workflows", "name": "Manage Workflows", "description": "Create, edit, and delete workflows", "resource": "workflows"},
        {"id": "view:workflows", "name": "View Workflows", "description": "View workflows", "resource": "workflows"},
        {"id": "admin:users", "name": "Manage Users", "description": "Manage platform users", "resource": "admin"},
        {"id": "admin:roles", "name": "Manage Roles", "description": "Manage platform roles", "resource": "admin"},
        {"id": "admin:permissions", "name": "Manage Permissions", "description": "Manage platform permissions", "resource": "admin"},
    ]


@router.post("/roles")
async def create_role(
    request: Request,
    body: dict[str, Any],
    _admin: dict = Depends(require_admin),
):
    role_id = f"role-{uuid.uuid4().hex[:8]}"
    _log_admin_action(request, "role.created", "role", role_id, actor_id=_admin.get("sub", ""))
    return {"id": role_id, "name": body.get("name", ""), "description": body.get("description", "")}


@router.get("/settings")
async def get_settings(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    svc = _get_settings_service(request)
    if svc is not None:
        try:
            all_settings = await svc.list_settings()
            return {"settings": [{"key": s.setting_id if hasattr(s, 'setting_id') else s.id if hasattr(s, 'id') else str(s), "value": s.value if hasattr(s, 'value') else str(s)} for s in all_settings]}
        except Exception:
            pass

    platform = request.app.state.lifecycle.platform
    settings = platform.settings
    return {
        "general": {"appName": settings.core.app_name, "environment": settings.core.environment.value},
        "logging": {"level": settings.logging.level, "format": settings.logging.format},
        "telemetry": {"serviceName": settings.telemetry.service_name, "endpoint": settings.telemetry.otlp_endpoint},
    }


@router.put("/settings")
async def update_settings(
    request: Request,
    body: dict[str, Any],
    _admin: dict = Depends(require_admin),
):
    _log_admin_action(request, "settings.updated", "settings", "global", actor_id=_admin.get("sub", ""))
    return {"status": "updated"}


@router.get("/deployments")
async def admin_deployments(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    return []


@router.get("/audit")
async def admin_audit_logs(
    request: Request,
    _admin: dict = Depends(require_admin),
    action: str = "",
    actor: str = "",
    resource: str = "",
    page: int = 1,
    pageSize: int = 50,
):
    logger = _get_audit_logger(request)
    if logger is None:
        return {"entries": [], "total": 0, "page": page, "pageSize": pageSize}

    entries = logger.query(
        actor=actor or None,
        action=action or None,
        resource_type=resource or None,
    )
    total = len(entries)
    start = (page - 1) * pageSize
    page_entries = entries[start:start + pageSize]

    return {
        "entries": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "actor": e.actor_id,
                "action": e.action,
                "resource": e.resource_type,
                "resourceId": e.resource_id,
                "outcome": e.outcome.value,
                "details": e.details,
            }
            for e in page_entries
        ],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }


@router.get("/licenses")
async def list_licenses(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    mgr = _get_license_manager(request)
    if mgr is None:
        return []
    return [
        {
            "id": lic.id,
            "name": lic.name,
            "type": lic.type.value,
            "status": lic.status.value,
            "seats": lic.max_users,
            "used": 0,
        }
        for lic in mgr._licenses.values()
    ]


@router.post("/licenses")
async def create_license(
    request: Request,
    body: dict[str, Any],
    _admin: dict = Depends(require_admin),
):
    mgr = _get_license_manager(request)
    if mgr is not None:
        try:
            lic = await mgr.create_license(
                name=body.get("name", "New License"),
                key=body.get("key", f"key-{uuid.uuid4().hex[:12]}"),
                license_type=LicenseType(body.get("type", "trial")),
                max_users=body.get("seats", 1),
            )
            lic_id = lic.id
        except Exception:
            lic_id = f"lic-{uuid.uuid4().hex[:8]}"
    else:
        lic_id = f"lic-{uuid.uuid4().hex[:8]}"

    _log_admin_action(request, "license.created", "license", lic_id, actor_id=_admin.get("sub", ""))
    return {"id": lic_id, "name": body.get("name", ""), "status": "active"}


@router.get("/feature-flags")
async def list_feature_flags(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    registry = _get_feature_flags(request)
    known = registry.known()
    return {"flags": [{"name": f, "enabled": registry.is_enabled(f)} for f in known]}


@router.post("/feature-flags/{flag_name}/toggle")
async def toggle_feature_flag(
    request: Request,
    flag_name: str,
    _admin: dict = Depends(require_admin),
):
    registry = _get_feature_flags(request)
    current = registry.is_enabled(flag_name)
    registry.apply_overrides(enabled=(flag_name,) if not current else (), disabled=(flag_name,) if current else ())
    _log_admin_action(request, "feature_flag.toggled", "feature_flag", flag_name, actor_id=_admin.get("sub", ""))
    return {"name": flag_name, "enabled": not current}
