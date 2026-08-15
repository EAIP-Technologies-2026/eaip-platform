"""Administration Center API — composes existing EAIP administrative services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_403_FORBIDDEN

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(
    prefix="/administration", tags=["administration"]
)
log = get_logger("eaip.http.routers.administration")


async def require_admin(request: Request, _user: dict = Depends(get_current_user)) -> dict:
    roles = _user.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Admin access required")
    return _user


@router.get("/overview")
async def administration_overview(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Aggregated administration overview from existing platform services."""
    container = request.app.state.lifecycle.platform.container

    from eaip.organization.service import OrganizationService
    from eaip.agents.registry import AgentRegistry
    from eaip.workflow.registry import WorkflowRegistry

    org_svc = container.try_resolve(OrganizationService)
    agent_reg = container.try_resolve(AgentRegistry)
    wf_reg = container.try_resolve(WorkflowRegistry)

    user_count = 0
    org_count = 0
    team_count = 0
    if org_svc:
        try:
            members = org_svc.list_members()
            user_count = len(members)
        except Exception:
            pass
        try:
            orgs = org_svc.list_organizations()
            org_count = len(orgs)
        except Exception:
            pass
        try:
            units = org_svc.list_units()
            team_count = len(units)
        except Exception:
            pass

    agent_count = 0
    if agent_reg:
        try:
            agents = await agent_reg.list_agents()
            agent_count = len(agents)
        except Exception:
            pass

    workflow_count = 0
    if wf_reg:
        try:
            wfs = await wf_reg.list_definitions()
            workflow_count = len(wfs)
        except Exception:
            pass

    return {
        "users": {"total": user_count},
        "organizations": {"total": org_count},
        "teams": {"total": team_count},
        "agents": {"total": agent_count},
        "workflows": {"total": workflow_count},
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/organization")
async def administration_organization(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Organization details from existing OrganizationService."""
    container = request.app.state.lifecycle.platform.container
    from eaip.organization.service import OrganizationService

    org_svc = container.try_resolve(OrganizationService)
    if org_svc is None:
        return {"organizations": []}

    try:
        orgs = org_svc.list_organizations()
        result = []
        for org in orgs:
            result.append({
                "id": getattr(org, "org_id", getattr(org, "id", "")),
                "name": getattr(org, "name", ""),
                "description": getattr(org, "description", ""),
                "status": getattr(org, "status", "active").value
                if hasattr(getattr(org, "status", ""), "value")
                else str(getattr(org, "status", "active")),
                "type": getattr(org, "type", "standard").value
                if hasattr(getattr(org, "type", ""), "value")
                else str(getattr(org, "type", "standard")),
                "memberCount": getattr(org, "member_count", 0),
                "createdAt": getattr(org, "created_at", datetime.now(UTC)).isoformat()
                if hasattr(getattr(org, "created_at", None), "isoformat")
                else datetime.now(UTC).isoformat(),
            })
        return {"organizations": result}
    except Exception as e:
        log.warning("organization.list_failed", error=str(e))
        return {"organizations": []}


@router.get("/teams")
async def administration_teams(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Teams/departments from existing OrganizationService."""
    container = request.app.state.lifecycle.platform.container
    from eaip.organization.service import OrganizationService

    org_svc = container.try_resolve(OrganizationService)
    if org_svc is None:
        return {"teams": []}

    try:
        units = org_svc.list_units()
        result = []
        for unit in units:
            result.append({
                "id": getattr(unit, "unit_id", getattr(unit, "id", "")),
                "name": getattr(unit, "name", ""),
                "description": getattr(unit, "description", ""),
                "type": getattr(unit, "type", "department").value
                if hasattr(getattr(unit, "type", ""), "value")
                else str(getattr(unit, "type", "department")),
                "memberCount": getattr(unit, "member_count", 0),
                "parentUnitId": getattr(unit, "parent_unit_id", None),
            })
        return {"teams": result}
    except Exception as e:
        log.warning("teams.list_failed", error=str(e))
        return {"teams": []}


@router.get("/quotas")
async def administration_quotas(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Quota information from existing tenant infrastructure."""
    container = request.app.state.lifecycle.platform.container
    from eaip.tenants.manager import TenantManager

    tenant_mgr = container.try_resolve(TenantManager)
    if tenant_mgr is None:
        return {"quotas": []}

    try:
        quotas = []
        for tenant in tenant_mgr._tenants.values():
            q = getattr(tenant, "quota", None)
            if q:
                quotas.append({
                    "tenantId": getattr(tenant, "tenant_id", getattr(tenant, "id", "")),
                    "tenantName": getattr(tenant, "name", ""),
                    "maxUsers": getattr(q, "max_users", 0),
                    "maxAgents": getattr(q, "max_agents", 0),
                    "maxWorkflows": getattr(q, "max_workflows", 0),
                    "maxStorageGb": getattr(q, "max_storage_gb", 0),
                    "status": getattr(tenant, "status", "active").value
                    if hasattr(getattr(tenant, "status", ""), "value")
                    else str(getattr(tenant, "status", "active")),
                })
        return {"quotas": quotas}
    except Exception as e:
        log.warning("quotas.list_failed", error=str(e))
        return {"quotas": []}


@router.get("/integrations")
async def administration_integrations(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Integration/connector status from existing ConnectorService."""
    container = request.app.state.lifecycle.platform.container
    from eaip.connectors.service import ConnectorService

    connector_svc = container.try_resolve(ConnectorService)
    if connector_svc is None:
        return {"integrations": []}

    try:
        connectors = connector_svc.list_connectors()
        result = []
        for c in connectors:
            result.append({
                "id": getattr(c, "connector_id", getattr(c, "id", "")),
                "name": getattr(c, "name", ""),
                "type": getattr(c, "connector_type", "unknown").value
                if hasattr(getattr(c, "connector_type", ""), "value")
                else str(getattr(c, "connector_type", "unknown")),
                "status": getattr(c, "status", "unknown").value
                if hasattr(getattr(c, "status", ""), "value")
                else str(getattr(c, "status", "unknown")),
                "description": getattr(c, "description", ""),
            })
        return {"integrations": result}
    except Exception as e:
        log.warning("integrations.list_failed", error=str(e))
        return {"integrations": []}


@router.get("/policies")
async def administration_policies(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Policy information from existing PolicyEngine."""
    container = request.app.state.lifecycle.platform.container
    from eaip.policy.registry import PolicyRegistry

    policy_reg = container.try_resolve(PolicyRegistry)
    if policy_reg is None:
        return {"policies": []}

    try:
        policies = policy_reg.list_policies()
        result = []
        for p in policies:
            result.append({
                "id": getattr(p, "policy_id", getattr(p, "id", "")),
                "name": getattr(p, "name", ""),
                "description": getattr(p, "description", ""),
                "effect": getattr(p, "effect", "allow").value
                if hasattr(getattr(p, "effect", ""), "value")
                else str(getattr(p, "effect", "allow")),
                "priority": getattr(p, "priority", 0),
                "enabled": getattr(p, "enabled", True),
                "ruleCount": len(getattr(p, "rules", [])),
            })
        return {"policies": result}
    except Exception as e:
        log.warning("policies.list_failed", error=str(e))
        return {"policies": []}


@router.get("/audit")
async def administration_audit(
    request: Request,
    _admin: dict = Depends(require_admin),
    action: str = "",
    actor: str = "",
    resource: str = "",
    page: int = 1,
    pageSize: int = 50,
):
    """Audit log from existing AuditLogger."""
    container = request.app.state.lifecycle.platform.container
    from eaip.admin.audit import AuditLogger

    logger = container.try_resolve(AuditLogger)
    if logger is None:
        return {"entries": [], "total": 0, "page": page, "pageSize": pageSize}

    entries = logger.query(
        actor=actor or None,
        action=action or None,
        resource_type=resource or None,
    )
    total = len(entries)
    start = (page - 1) * pageSize
    page_entries = entries[start : start + pageSize]

    return {
        "entries": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat()
                if hasattr(e.timestamp, "isoformat")
                else datetime.now(UTC).isoformat(),
                "actor": e.actor_id,
                "action": e.action,
                "resource": e.resource_type,
                "resourceId": e.resource_id,
                "outcome": e.outcome.value
                if hasattr(e.outcome, "value")
                else str(e.outcome),
                "details": e.details,
            }
            for e in page_entries
        ],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }


@router.get("/feature-flags")
async def administration_feature_flags(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Feature flags from existing FeatureFlagRegistry."""
    container = request.app.state.lifecycle.platform.container
    registry = container.feature_flags if hasattr(container, "feature_flags") else None
    if registry is None:
        from eaip.core.feature_flags import FeatureFlagRegistry
        registry = container.try_resolve(FeatureFlagRegistry)

    if registry is None:
        return {"flags": []}

    known = registry.known()
    return {
        "flags": [
            {"name": f, "enabled": registry.is_enabled(f)}
            for f in known
        ]
    }


@router.post("/feature-flags/{flag_name}/toggle")
async def toggle_feature_flag(
    request: Request,
    flag_name: str,
    _admin: dict = Depends(require_admin),
):
    """Toggle a feature flag."""
    container = request.app.state.lifecycle.platform.container
    registry = container.feature_flags if hasattr(container, "feature_flags") else None
    if registry is None:
        from eaip.core.feature_flags import FeatureFlagRegistry
        registry = container.try_resolve(FeatureFlagRegistry)

    if registry is None:
        raise HTTPException(status_code=404, detail="Feature flag registry not available")

    current = registry.is_enabled(flag_name)
    registry.apply_overrides(
        enabled=(flag_name,) if not current else (),
        disabled=(flag_name,) if current else (),
    )
    return {"name": flag_name, "enabled": not current}


@router.get("/settings")
async def administration_settings(
    request: Request,
    _admin: dict = Depends(require_admin),
):
    """Platform settings from existing EnterpriseSettingsService."""
    container = request.app.state.lifecycle.platform.container
    from eaip.enterprise_settings.service import EnterpriseSettingsService

    svc = container.try_resolve(EnterpriseSettingsService)
    if svc is not None:
        try:
            all_settings = await svc.list_settings()
            return {
                "settings": [
                    {
                        "key": s.setting_id
                        if hasattr(s, "setting_id")
                        else s.id
                        if hasattr(s, "id")
                        else str(s),
                        "value": s.value if hasattr(s, "value") else str(s),
                    }
                    for s in all_settings
                ]
            }
        except Exception:
            pass

    platform = request.app.state.lifecycle.platform
    settings = platform.settings
    return {
        "general": {
            "appName": settings.core.app_name,
            "environment": settings.core.environment.value,
        },
        "logging": {
            "level": settings.logging.level,
            "format": settings.logging.format,
        },
    }
