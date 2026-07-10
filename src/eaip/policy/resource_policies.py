"""Resource, Tool, Department, and Workflow policy models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.policy.models import PolicyEffect, PolicyRule
from eaip.shared.time import utc_now


class ResourcePolicy(BaseModel):
    """Policy governing access to specific resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    resource_type: str = ""
    resource_pattern: str = "*"
    allowed_actions: tuple[str, ...] = Field(default_factory=tuple)
    denied_actions: tuple[str, ...] = Field(default_factory=tuple)
    rules: tuple[PolicyRule, ...] = Field(default_factory=tuple)
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)


class ToolAccessLevel(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    RESTRICTED = "restricted"


class ToolPolicy(BaseModel):
    """Policy governing tool usage by agents and workflows."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    tool_pattern: str = "*"
    access_level: ToolAccessLevel = ToolAccessLevel.ALLOW
    allowed_parameters: dict[str, list[Any]] = Field(default_factory=dict)
    max_execution_seconds: float = 0.0
    rate_limit_per_minute: int = 0
    roles: tuple[str, ...] = Field(default_factory=tuple)
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)


class DepartmentPolicy(BaseModel):
    """Policy governing a business department/tenant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    department_id: str
    resource_policies: tuple[str, ...] = Field(default_factory=tuple)
    tool_policies: tuple[str, ...] = Field(default_factory=tuple)
    workflow_policies: tuple[str, ...] = Field(default_factory=tuple)
    approval_policies: tuple[str, ...] = Field(default_factory=tuple)
    max_concurrent_workflows: int = 0
    max_agent_runs_per_minute: int = 0
    enabled: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


class WorkflowPolicy(BaseModel):
    """Policy governing workflow execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    workflow_pattern: str = "*"
    max_duration_seconds: float = 0.0
    max_steps: int = 0
    allowed_agent_ids: tuple[str, ...] = Field(default_factory=tuple)
    denied_agent_ids: tuple[str, ...] = Field(default_factory=tuple)
    allowed_tool_names: tuple[str, ...] = Field(default_factory=tuple)
    denied_tool_names: tuple[str, ...] = Field(default_factory=tuple)
    require_approval_for_steps: tuple[str, ...] = Field(default_factory=tuple)
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)


class ApprovalPolicy(BaseModel):
    """Policy governing approval routing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    trigger_conditions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    required_approvers: tuple[str, ...] = Field(default_factory=tuple)
    min_approvals_required: int = 1
    timeout_seconds: float = 86400.0
    escalation_after_seconds: float = 0.0
    escalation_approvers: tuple[str, ...] = Field(default_factory=tuple)
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)


class PolicyEvaluationReport(BaseModel):
    """Detailed report of a policy evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str
    subject_id: str
    action: str
    resource: str
    effect: PolicyEffect
    matched_policies: tuple[str, ...] = Field(default_factory=tuple)
    matched_rules: tuple[str, ...] = Field(default_factory=tuple)
    evaluation_time_ms: float = 0.0
    evaluated_at: datetime = Field(default_factory=utc_now)
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    errors: tuple[str, ...] = Field(default_factory=tuple)


__all__ = [
    "ApprovalPolicy",
    "DepartmentPolicy",
    "PolicyEvaluationReport",
    "ResourcePolicy",
    "ToolAccessLevel",
    "ToolPolicy",
    "WorkflowPolicy",
]
