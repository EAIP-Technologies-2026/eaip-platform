"""Governance and Compliance API Routes."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_403_FORBIDDEN

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger

router = APIRouter(prefix="/governance", tags=["governance"])
log = get_logger("eaip.http.routers.governance")


async def require_admin(request: Request, _user: dict = Depends(get_current_user)) -> dict:
    """Ensure the user has admin roles."""
    roles = _user.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Admin access required")
    return _user


@router.get("/policies")
async def list_policies(request: Request, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    """List all registered policies in the PolicyEngine."""
    container = request.app.state.lifecycle.platform.container
    from eaip.policy.integration import PolicyRuntimeModule
    
    policy_mod = container.try_resolve(PolicyRuntimeModule)
    if not policy_mod:
        return {"policies": [], "total": 0}
        
    registry = policy_mod.registry
    policies = registry.all()
    
    return {
        "policies": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "enabled": p.enabled,
                "type": p.__class__.__name__
            } for p in policies
        ],
        "total": len(policies)
    }


@router.get("/guardrails")
async def get_guardrail_status(request: Request, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    """Get the status of AI guardrails."""
    container = request.app.state.lifecycle.platform.container
    from eaip.guardrails.integration import GuardrailRuntimeModule
    
    guardrail_mod = container.try_resolve(GuardrailRuntimeModule)
    if not guardrail_mod:
        return {"status": "unavailable", "engine": None}
        
    health = await guardrail_mod.health_check.check()
    return {
        "status": health.status.value if hasattr(health.status, "value") else str(health.status),
        "details": health.details,
    }


@router.get("/compliance")
async def get_compliance_status(request: Request, _admin: dict = Depends(require_admin)) -> dict[str, Any]:
    """Get the overall compliance framework status."""
    container = request.app.state.lifecycle.platform.container
    from eaip.compliance.integration import ComplianceRuntimeModule
    
    comp_mod = container.try_resolve(ComplianceRuntimeModule)
    if not comp_mod:
        return {"status": "unavailable"}
        
    try:
        health = await comp_mod.health_check.check()
        return {
            "status": health.status.value if hasattr(health.status, "value") else str(health.status),
            "details": health.details,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
