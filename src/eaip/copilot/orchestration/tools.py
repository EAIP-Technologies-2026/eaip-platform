"""Governed orchestration tools for EAIP Conductor Phase 10.

These tools compose existing platform infrastructure to create and
manage orchestration plans.  They do NOT bypass governance.
"""

from __future__ import annotations

import json

from pydantic.json_schema import JsonSchemaValue

from eaip.copilot.models import RiskTier
from eaip.copilot.orchestration.models import (
    CreatePlanRequest,
    PlanRisk,
    PlanStatus,
)
from eaip.copilot.orchestration.service import OrchestrationService
from eaip.tools.base import Tool


class CreateOrchestrationPlanTool:
    """Create a new governed orchestration plan."""

    name = "create_orchestration_plan"
    description = (
        "Create a new orchestration plan with bounded steps."
    )
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:orchestration:write"

    def __init__(self, service: OrchestrationService) -> None:
        """Initialize with the orchestration service."""
        self._service = service

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for plan creation arguments."""
        return {
            "type": "object",
            "properties": {
                "objective": {
                    "type": "string",
                    "description": "The plan objective.",
                },
                "description": {
                    "type": "string",
                    "default": "",
                },
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "description": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "risk": {
                                "type": "string",
                                "enum": [
                                    "informational",
                                    "action",
                                    "destructive",
                                ],
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "approval_required": {
                                "type": "boolean",
                            },
                            "reversible": {"type": "boolean"},
                            "rollback_tool": {"type": "string"},
                        },
                        "required": ["id", "description"],
                    },
                },
                "estimated_risk": {
                    "type": "string",
                    "enum": ["informational", "action", "destructive"],
                    "default": "informational",
                },
            },
            "required": ["objective"],
        }

    async def execute(self, **kwargs: object) -> str:
        """Create a plan and return its details."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        objective = str(kwargs.get("objective", "")).strip()
        if not objective:
            return json.dumps(
                {"error": "objective is required"}
            )
        description = str(kwargs.get("description", ""))
        steps_raw = kwargs.get("steps", [])
        steps = list(steps_raw) if isinstance(steps_raw, list) else []
        risk_str = str(
            kwargs.get("estimated_risk", "informational")
        ).lower()
        try:
            risk = PlanRisk(risk_str)
        except ValueError:
            risk = PlanRisk.INFORMATIONAL

        request = CreatePlanRequest(
            objective=objective,
            description=description,
            steps=steps,
            estimated_risk=risk,
        )
        try:
            plan = await self._service.create(user, request)
        except (ValueError, PermissionError) as exc:
            return json.dumps({"error": str(exc)})
        return json.dumps(self._service.serialize(plan), default=str)


class ListOrchestrationPlansTool:
    """List orchestration plans."""

    name = "list_orchestration_plans"
    description = "List orchestration plans."
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:orchestration:read"

    def __init__(self, service: OrchestrationService) -> None:
        """Initialize with the orchestration service."""
        self._service = service

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for list arguments."""
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        }

    async def execute(self, **kwargs: object) -> str:
        """List plans visible to the user."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        limit = int(str(kwargs.get("limit", 10)))
        status_str = str(kwargs.get("status", "")).strip()
        status = None
        if status_str:
            try:
                status = PlanStatus(status_str)
            except ValueError:
                pass
        plans = await self._service.list_plans(
            user, status=status, limit=limit
        )
        return json.dumps(
            [self._service.serialize(p) for p in plans],
            default=str,
        )


class GetOrchestrationPlanTool:
    """Get orchestration plan details."""

    name = "get_orchestration_plan"
    description = "Get details for a specific plan."
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:orchestration:read"

    def __init__(self, service: OrchestrationService) -> None:
        """Initialize with the orchestration service."""
        self._service = service

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for get arguments."""
        return {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
            },
            "required": ["plan_id"],
        }

    async def execute(self, **kwargs: object) -> str:
        """Get a plan by ID."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        plan_id = str(kwargs.get("plan_id", "")).strip()
        if not plan_id:
            return json.dumps({"error": "plan_id is required"})
        plan = await self._service.get(user, plan_id)
        if plan is None:
            return json.dumps({"error": "Plan not found"})
        return json.dumps(
            self._service.serialize(plan), default=str
        )


def build_orchestration_tools(
    *,
    orchestration_service: OrchestrationService,
) -> dict[str, Tool]:
    """Build the orchestration tool set for Conductor."""
    tools: list[Tool] = [
        CreateOrchestrationPlanTool(orchestration_service),
        ListOrchestrationPlansTool(orchestration_service),
        GetOrchestrationPlanTool(orchestration_service),
    ]
    return {tool.name: tool for tool in tools}


__all__ = [
    "CreateOrchestrationPlanTool",
    "GetOrchestrationPlanTool",
    "ListOrchestrationPlansTool",
    "build_orchestration_tools",
]
