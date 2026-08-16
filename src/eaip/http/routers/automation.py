"""REST API routes for Automation Rules."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from eaip.automation.engine import AutomationEngine
from eaip.automation.exceptions import RuleNotFoundError
from eaip.automation.models import AutomationRule, TriggerType
from eaip.http.dependencies import get_tenant_id

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


class RegisterRuleRequest(BaseModel):
    rule: AutomationRule


def get_automation_engine(request: Request) -> AutomationEngine:
    return request.app.state.lifecycle.platform.container.resolve(AutomationEngine)


@router.post("/rules", response_model=AutomationRule, status_code=status.HTTP_201_CREATED)
async def register_rule(
    req: RegisterRuleRequest,
    engine: AutomationEngine = Depends(get_automation_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Register a new automation rule."""
    try:
        # Engine registers rule directly
        await engine.register_rule(req.rule, tenant_id=tenant_id)
        return req.rule
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/rules", response_model=list[AutomationRule])
async def list_rules(
    trigger_type: TriggerType | None = None,
    enabled: bool | None = None,
    engine: AutomationEngine = Depends(get_automation_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """List automation rules, optionally filtered by trigger_type or status."""
    return await engine.list_rules(trigger_type=trigger_type, enabled=enabled, tenant_id=tenant_id)


@router.get("/rules/{rule_id}", response_model=AutomationRule)
async def get_rule(
    rule_id: str,
    engine: AutomationEngine = Depends(get_automation_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get a specific automation rule."""
    try:
        return await engine.get_rule(rule_id, tenant_id=tenant_id)
    except RuleNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_rule(
    rule_id: str,
    engine: AutomationEngine = Depends(get_automation_engine),
    tenant_id: str = Depends(get_tenant_id),
):
    """Unregister/delete a specific automation rule."""
    try:
        await engine.unregister_rule(rule_id, tenant_id=tenant_id)
    except RuleNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
