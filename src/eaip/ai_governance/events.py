"""Domain events for AI Governance & Compliance."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class AiGovernancePolicyCreated(DomainEvent):
    """Published when a new AI governance policy is created."""

    event_type: ClassVar[str] = "eaip.ai_governance.policy.created"

    policy_id: str
    policy_name: str
    policy_type: str


class AiGovernancePolicyUpdated(DomainEvent):
    """Published when an AI governance policy is updated."""

    event_type: ClassVar[str] = "eaip.ai_governance.policy.updated"

    policy_id: str
    policy_name: str
    changes: dict[str, Any] = Field(default_factory=dict)


class AiGovernancePolicyEnforced(DomainEvent):
    """Published when an AI governance policy is enforced."""

    event_type: ClassVar[str] = "eaip.ai_governance.policy.enforced"

    policy_id: str
    policy_name: str
    subject_id: str
    action: str
    resource: str
    matched_rules: tuple[str, ...] = ()


class AiGovernancePolicyViolated(DomainEvent):
    """Published when an AI governance policy is violated."""

    event_type: ClassVar[str] = "eaip.ai_governance.policy.violated"

    policy_id: str
    policy_name: str
    subject_id: str
    action: str
    resource: str
    explanation: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class AiComplianceCheckStarted(DomainEvent):
    """Published when a compliance check begins."""

    event_type: ClassVar[str] = "eaip.ai_governance.compliance.check_started"

    check_id: str
    requirement_id: str
    standard: str


class AiComplianceCheckCompleted(DomainEvent):
    """Published when a compliance check completes successfully."""

    event_type: ClassVar[str] = "eaip.ai_governance.compliance.check_completed"

    check_id: str
    requirement_id: str
    status: str
    score: float = 0.0


class AiComplianceCheckFailed(DomainEvent):
    """Published when a compliance check fails."""

    event_type: ClassVar[str] = "eaip.ai_governance.compliance.check_failed"

    check_id: str
    requirement_id: str
    error: str = ""


class AiComplianceReportGenerated(DomainEvent):
    """Published when a compliance report is generated."""

    event_type: ClassVar[str] = "eaip.ai_governance.compliance.report_generated"

    report_id: str
    standard: str
    overall_status: str
    score: float = 0.0


class AiComplianceRequirementUpdated(DomainEvent):
    """Published when a compliance requirement is updated."""

    event_type: ClassVar[str] = "eaip.ai_governance.compliance.requirement_updated"

    requirement_id: str
    name: str
    old_status: str = ""
    new_status: str = ""


class AiAuditTrailEntryCreated(DomainEvent):
    """Published when a new audit trail entry is created."""

    event_type: ClassVar[str] = "eaip.ai_governance.audit.entry_created"

    entry_id: str
    action: str
    actor: str = ""
    resource_id: str = ""
    resource_type: str = ""


class AiGovernanceReviewStarted(DomainEvent):
    """Published when a governance review is started."""

    event_type: ClassVar[str] = "eaip.ai_governance.review.started"

    review_id: str
    resource_id: str
    resource_type: str
    reviewer: str = ""


class AiGovernanceReviewCompleted(DomainEvent):
    """Published when a governance review is completed."""

    event_type: ClassVar[str] = "eaip.ai_governance.review.completed"

    review_id: str
    resource_id: str
    decision: str = ""
    status: str = ""


class AiGovernanceReviewApproved(DomainEvent):
    """Published when a governance review is approved."""

    event_type: ClassVar[str] = "eaip.ai_governance.review.approved"

    review_id: str
    resource_id: str
    reviewer: str = ""
    comments: str = ""


class AiGovernanceReviewRejected(DomainEvent):
    """Published when a governance review is rejected."""

    event_type: ClassVar[str] = "eaip.ai_governance.review.rejected"

    review_id: str
    resource_id: str
    reviewer: str = ""
    comments: str = ""


class AiBiasCheckCompleted(DomainEvent):
    """Published when a bias detection check completes."""

    event_type: ClassVar[str] = "eaip.ai_governance.bias.check_completed"

    check_id: str
    model_id: str
    bias_score: float = 0.0
    biased: bool = False


class AiFairnessMetricComputed(DomainEvent):
    """Published when a fairness metric is computed."""

    event_type: ClassVar[str] = "eaip.ai_governance.fairness.metric_computed"

    metric_id: str
    model_id: str
    metric_name: str
    value: float = 0.0
    passed: bool = False


class AiModelRiskAssessed(DomainEvent):
    """Published when an AI model risk assessment is performed."""

    event_type: ClassVar[str] = "eaip.ai_governance.risk.assessed"

    assessment_id: str
    model_id: str
    model_name: str
    risk_level: str
    risk_score: float = 0.0


class AiGovernanceDashboardUpdated(DomainEvent):
    """Published when the governance dashboard is updated."""

    event_type: ClassVar[str] = "eaip.ai_governance.dashboard.updated"

    dashboard_id: str
    overall_compliance_score: float = 0.0
    total_policies: int = 0


__all__ = [
    "AiAuditTrailEntryCreated",
    "AiBiasCheckCompleted",
    "AiComplianceCheckCompleted",
    "AiComplianceCheckFailed",
    "AiComplianceCheckStarted",
    "AiComplianceReportGenerated",
    "AiComplianceRequirementUpdated",
    "AiFairnessMetricComputed",
    "AiGovernanceDashboardUpdated",
    "AiGovernancePolicyCreated",
    "AiGovernancePolicyEnforced",
    "AiGovernancePolicyUpdated",
    "AiGovernancePolicyViolated",
    "AiGovernanceReviewApproved",
    "AiGovernanceReviewCompleted",
    "AiGovernanceReviewRejected",
    "AiGovernanceReviewStarted",
    "AiModelRiskAssessed",
]
