"""Knowledge Governance domain events."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class KnowledgeGovernanceEvent(DomainEvent):
    """Base event for all Knowledge Governance events."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.event"


class KnowledgeGovernancePolicyCreated(KnowledgeGovernanceEvent):
    """Published when a governance policy is created."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.policy.created"
    policy_id: str
    policy_name: str
    scope: str = ""


class KnowledgeGovernancePolicyUpdated(KnowledgeGovernanceEvent):
    """Published when a governance policy is updated."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.policy.updated"
    policy_id: str
    policy_name: str
    changes: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGovernancePolicyEnforced(KnowledgeGovernanceEvent):
    """Published when a governance policy is enforced."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.policy.enforced"
    policy_id: str
    policy_name: str
    subject_id: str
    action: str
    resource: str
    matched_rules: tuple[str, ...] = ()


class KnowledgeGovernancePolicyViolated(KnowledgeGovernanceEvent):
    """Published when a governance policy is violated."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.policy.violated"
    policy_id: str
    policy_name: str
    subject_id: str
    action: str
    resource: str
    explanation: str = ""


class KnowledgeQualityCheckStarted(KnowledgeGovernanceEvent):
    """Published when a quality check starts."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.quality_check.started"
    check_id: str
    resource_id: str
    resource_type: str


class KnowledgeQualityCheckCompleted(KnowledgeGovernanceEvent):
    """Published when a quality check completes successfully."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.quality_check.completed"
    check_id: str
    resource_id: str
    resource_type: str
    overall_score: float
    passed: bool


class KnowledgeQualityCheckFailed(KnowledgeGovernanceEvent):
    """Published when a quality check fails."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.quality_check.failed"
    check_id: str
    resource_id: str
    resource_type: str
    error: str = ""


class KnowledgeQualityScoreComputed(KnowledgeGovernanceEvent):
    """Published when an aggregated quality score is computed."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.quality_score.computed"
    score_id: str
    resource_id: str
    resource_type: str
    score: float


class KnowledgeAuditTrailEntryCreated(KnowledgeGovernanceEvent):
    """Published when an audit trail entry is created."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.audit_trail.entry_created"
    entry_id: str
    action: str
    actor: str
    resource_id: str


class KnowledgeGovernanceReportGenerated(KnowledgeGovernanceEvent):
    """Published when a governance report is generated."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.report.generated"
    report_id: str
    report_type: str


class KnowledgeRetentionRuleApplied(KnowledgeGovernanceEvent):
    """Published when a retention rule is applied to resources."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.retention_rule.applied"
    rule_id: str
    rule_name: str
    resource_count: int
    action: str


class KnowledgeClassificationUpdated(KnowledgeGovernanceEvent):
    """Published when a resource classification is updated."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.classification.updated"
    resource_id: str
    resource_type: str
    previous_level: str
    new_level: str


class KnowledgeSourceValidated(KnowledgeGovernanceEvent):
    """Published when a knowledge source is validated."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.source.validated"
    validation_id: str
    source_id: str
    source_type: str


class KnowledgeSourceApproved(KnowledgeGovernanceEvent):
    """Published when a knowledge source is approved."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.source.approved"
    validation_id: str
    source_id: str
    source_type: str


class KnowledgeSourceRejected(KnowledgeGovernanceEvent):
    """Published when a knowledge source is rejected."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.source.rejected"
    validation_id: str
    source_id: str
    source_type: str
    reason: str = ""


class KnowledgeStewardshipAssigned(KnowledgeGovernanceEvent):
    """Published when a stewardship role is assigned."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.stewardship.assigned"
    assignment_id: str
    resource_id: str
    user_id: str
    role: str


class KnowledgeStewardshipUnassigned(KnowledgeGovernanceEvent):
    """Published when a stewardship role is unassigned."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.stewardship.unassigned"
    assignment_id: str
    resource_id: str
    user_id: str
    role: str


class KnowledgeGovernanceDashboardUpdated(KnowledgeGovernanceEvent):
    """Published when the governance dashboard is updated."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.dashboard.updated"
    dashboard_id: str
    overall_quality_score: float
    total_policies: int


class KnowledgeGovernanceConfigUpdated(KnowledgeGovernanceEvent):
    """Published when governance configuration is updated."""

    event_type: ClassVar[str] = "eaip.knowledge_governance.config.updated"
    config_id: str
    config_name: str


__all__ = [
    "KnowledgeAuditTrailEntryCreated",
    "KnowledgeClassificationUpdated",
    "KnowledgeGovernanceConfigUpdated",
    "KnowledgeGovernanceDashboardUpdated",
    "KnowledgeGovernanceEvent",
    "KnowledgeGovernancePolicyCreated",
    "KnowledgeGovernancePolicyEnforced",
    "KnowledgeGovernancePolicyUpdated",
    "KnowledgeGovernancePolicyViolated",
    "KnowledgeGovernanceReportGenerated",
    "KnowledgeQualityCheckCompleted",
    "KnowledgeQualityCheckFailed",
    "KnowledgeQualityCheckStarted",
    "KnowledgeQualityScoreComputed",
    "KnowledgeRetentionRuleApplied",
    "KnowledgeSourceApproved",
    "KnowledgeSourceRejected",
    "KnowledgeSourceValidated",
    "KnowledgeStewardshipAssigned",
    "KnowledgeStewardshipUnassigned",
]
