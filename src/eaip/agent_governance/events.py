"""Agent governance domain events."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.shared.time import utc_now


class AgentGovernancePolicyCreated(DomainEvent):
    """Published when a governance policy is created."""

    event_type: ClassVar[str] = "eaip.agent_governance.policy.created"

    policy_id: str
    policy_name: str


class AgentGovernancePolicyUpdated(DomainEvent):
    """Published when a governance policy is updated."""

    event_type: ClassVar[str] = "eaip.agent_governance.policy.updated"

    policy_id: str
    policy_name: str


class AgentGovernancePolicyEnforced(DomainEvent):
    """Published when a governance policy is enforced on an agent."""

    event_type: ClassVar[str] = "eaip.agent_governance.policy.enforced"

    policy_id: str
    agent_id: str
    action: str


class AgentGovernancePolicyViolated(DomainEvent):
    """Published when a governance policy is violated."""

    event_type: ClassVar[str] = "eaip.agent_governance.policy.violated"

    policy_id: str
    agent_id: str
    action: str
    detail: str = ""


class AgentPermissionChanged(DomainEvent):
    """Published when an agent's permissions change."""

    event_type: ClassVar[str] = "eaip.agent_governance.permission.changed"

    agent_id: str
    permission_id: str
    change: str


class AgentActivityLogged(DomainEvent):
    """Published when an agent activity is logged."""

    event_type: ClassVar[str] = "eaip.agent_governance.activity.logged"

    log_id: str
    agent_id: str
    action: str


class AgentApprovalRequestCreated(DomainEvent):
    """Published when an approval request is created."""

    event_type: ClassVar[str] = "eaip.agent_governance.approval.request.created"

    request_id: str
    agent_id: str
    action: str


class AgentApprovalRequestApproved(DomainEvent):
    """Published when an approval request is approved."""

    event_type: ClassVar[str] = "eaip.agent_governance.approval.request.approved"

    request_id: str
    agent_id: str
    approved_by: str


class AgentApprovalRequestRejected(DomainEvent):
    """Published when an approval request is rejected."""

    event_type: ClassVar[str] = "eaip.agent_governance.approval.request.rejected"

    request_id: str
    agent_id: str
    rejected_by: str
    reason: str = ""


class AgentRestrictionApplied(DomainEvent):
    """Published when a restriction is applied to an agent."""

    event_type: ClassVar[str] = "eaip.agent_governance.restriction.applied"

    restriction_id: str
    agent_id: str
    restriction_type: str


class AgentUsagePolicyUpdated(DomainEvent):
    """Published when a usage policy is updated."""

    event_type: ClassVar[str] = "eaip.agent_governance.usage_policy.updated"

    policy_id: str
    policy_name: str


class AgentSopCreated(DomainEvent):
    """Published when an SOP is created."""

    event_type: ClassVar[str] = "eaip.agent_governance.sop.created"

    sop_id: str
    sop_name: str


class AgentSopUpdated(DomainEvent):
    """Published when an SOP is updated."""

    event_type: ClassVar[str] = "eaip.agent_governance.sop.updated"

    sop_id: str
    sop_name: str
    version: int


class AgentSopActivated(DomainEvent):
    """Published when an SOP is activated."""

    event_type: ClassVar[str] = "eaip.agent_governance.sop.activated"

    sop_id: str
    sop_name: str


class AgentComplianceCheckCompleted(DomainEvent):
    """Published when a compliance check completes successfully."""

    event_type: ClassVar[str] = "eaip.agent_governance.compliance.check.completed"

    check_id: str
    agent_id: str
    passed: bool


class AgentComplianceCheckFailed(DomainEvent):
    """Published when a compliance check fails."""

    event_type: ClassVar[str] = "eaip.agent_governance.compliance.check.failed"

    check_id: str
    agent_id: str
    error: str = ""


class AgentEscalationTriggered(DomainEvent):
    """Published when an escalation is triggered."""

    event_type: ClassVar[str] = "eaip.agent_governance.escalation.triggered"

    rule_id: str
    agent_id: str
    reason: str = ""
    triggered_at: datetime = Field(default_factory=utc_now)


class AgentGovernanceConfigUpdated(DomainEvent):
    """Published when the governance config is updated."""

    event_type: ClassVar[str] = "eaip.agent_governance.config.updated"

    config_id: str
    config_name: str


__all__ = [
    "AgentActivityLogged",
    "AgentApprovalRequestApproved",
    "AgentApprovalRequestCreated",
    "AgentApprovalRequestRejected",
    "AgentComplianceCheckCompleted",
    "AgentComplianceCheckFailed",
    "AgentEscalationTriggered",
    "AgentGovernanceConfigUpdated",
    "AgentGovernancePolicyCreated",
    "AgentGovernancePolicyEnforced",
    "AgentGovernancePolicyUpdated",
    "AgentGovernancePolicyViolated",
    "AgentPermissionChanged",
    "AgentRestrictionApplied",
    "AgentSopActivated",
    "AgentSopCreated",
    "AgentSopUpdated",
    "AgentUsagePolicyUpdated",
]
