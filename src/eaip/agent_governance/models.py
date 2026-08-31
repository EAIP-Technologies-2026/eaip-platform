"""Agent governance models — policies, permissions, approvals, SOPs, compliance."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AgentAccessScope(StrEnum):
    """Scope of access an agent is granted."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    EXECUTE = "execute"
    DEPLOY = "deploy"


class AgentApprovalStatus(StrEnum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AgentSopStatus(StrEnum):
    """Lifecycle status of a standard operating procedure."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class AgentPermission(BaseModel):
    """A permission granted to an agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    agent_id: str
    scope: AgentAccessScope
    resource: str
    granted_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    revoked: bool = False


class AgentCapability(BaseModel):
    """A capability that an agent may possess."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    enabled: bool = True


class AgentGovernanceRule(BaseModel):
    """A single governance rule for agents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    effect: str = "deny"
    actions: tuple[str, ...] = ()
    resources: tuple[str, ...] = ()
    conditions: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0


class AgentGovernancePolicy(BaseModel):
    """A policy that governs agent behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    rules: tuple[AgentGovernanceRule, ...] = ()
    enabled: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AgentActivityLog(BaseModel):
    """Log entry for an agent action."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    agent_id: str
    action: str
    resource: str
    outcome: str = ""
    detail: str = ""
    performed_at: datetime = Field(default_factory=utc_now)


class AgentAuditEntry(BaseModel):
    """Audit entry for governance-related changes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    agent_id: str
    change_type: str
    previous_state: dict[str, Any] = Field(default_factory=dict)
    new_state: dict[str, Any] = Field(default_factory=dict)
    changed_by: str = ""
    changed_at: datetime = Field(default_factory=utc_now)


class AgentApprovalConfig(BaseModel):
    """Configuration for how approvals work."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    approvers: tuple[str, ...] = ()
    required_approvals: int = 1
    timeout_seconds: int = 3600
    escalation_enabled: bool = False
    escalation_delay_seconds: int = 300


class AgentApprovalRequest(BaseModel):
    """A request for approval of an agent action."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    agent_id: str
    action: str
    resource: str
    rationale: str = ""
    status: AgentApprovalStatus = AgentApprovalStatus.PENDING
    requested_by: str = ""
    approved_by: str | None = None
    rejected_by: str | None = None
    rejection_reason: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None


class AgentRestriction(BaseModel):
    """A restriction placed on an agent's behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    agent_id: str
    restriction_type: str
    value: str = ""
    reason: str = ""
    applied_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None


class AgentUsagePolicy(BaseModel):
    """Policy governing how an agent may be used."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    max_concurrent_runs: int = 5
    max_daily_runs: int = 100
    max_duration_seconds: int = 3600
    allowed_sources: tuple[str, ...] = ()
    rate_limit_per_minute: int = 10
    enabled: bool = True


class AgentSop(BaseModel):
    """A standard operating procedure for an agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    steps: tuple[str, ...] = ()
    status: AgentSopStatus = AgentSopStatus.DRAFT
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AgentComplianceCheck(BaseModel):
    """Definition of a compliance check for agents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    check_type: str = ""
    rules: tuple[str, ...] = ()
    enabled: bool = True


class AgentComplianceResult(BaseModel):
    """Result of a compliance check execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    check_id: str
    agent_id: str
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=utc_now)


class AgentEscalationRule(BaseModel):
    """Rule that defines when and how to escalate governance issues."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    condition: str = ""
    target: str = ""
    priority: int = 0
    enabled: bool = True


class AgentGovernanceConfig(BaseModel):
    """Top-level governance configuration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    auditing_enabled: bool = True
    approvals_enabled: bool = True
    compliance_enabled: bool = True
    restrictions_enabled: bool = True
    sop_enabled: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


__all__ = [
    "AgentAccessScope",
    "AgentActivityLog",
    "AgentApprovalConfig",
    "AgentApprovalRequest",
    "AgentApprovalStatus",
    "AgentAuditEntry",
    "AgentCapability",
    "AgentComplianceCheck",
    "AgentComplianceResult",
    "AgentEscalationRule",
    "AgentGovernanceConfig",
    "AgentGovernancePolicy",
    "AgentGovernanceRule",
    "AgentPermission",
    "AgentRestriction",
    "AgentSop",
    "AgentSopStatus",
    "AgentUsagePolicy",
]
