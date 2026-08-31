"""Pydantic models for AI Governance & Compliance."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PolicyType(StrEnum):
    """Type of AI governance policy."""

    USAGE = "usage"
    SAFETY = "safety"
    ETHICS = "ethics"
    COMPLIANCE = "compliance"
    DATA = "data"
    MODEL = "model"
    ACCESS = "access"


class RiskLevel(StrEnum):
    """Risk level for AI model risk assessment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(StrEnum):
    """Status of a compliance check or requirement."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    """Status of an AI governance review."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ComplianceStandard(StrEnum):
    """Compliance standard for AI governance."""

    ISO_42001 = "iso_42001"
    EU_AI_ACT = "eu_ai_act"
    NIST_AI_RMF = "nist_ai_rmf"
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    CUSTOM = "custom"


class AiGovernanceRule(BaseModel):
    """A single rule within an AI governance policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    policy_type: PolicyType
    conditions: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, str] = {}


class AiGovernancePolicy(BaseModel):
    """An AI governance policy containing rules for governing AI usage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    policy_type: PolicyType
    rules: tuple[AiGovernanceRule, ...] = ()
    enabled: bool = True
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = {}


class AiComplianceRequirement(BaseModel):
    """A compliance requirement derived from a standard or regulation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    standard: ComplianceStandard
    control_id: str = ""
    category: str = ""
    severity: str = "medium"
    status: ComplianceStatus = ComplianceStatus.PENDING


class AiComplianceCheck(BaseModel):
    """A compliance check run against a requirement or control."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    requirement_id: str
    name: str
    description: str = ""
    status: ComplianceStatus = ComplianceStatus.PENDING
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    details: dict[str, Any] = {}


class AiComplianceResult(BaseModel):
    """Result of an AI compliance check evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    check_id: str
    requirement_id: str
    status: ComplianceStatus
    score: float = 0.0
    summary: str = ""
    details: dict[str, Any] = {}
    evaluated_at: datetime = Field(default_factory=utc_now)


class AiComplianceReport(BaseModel):
    """A report summarising AI compliance check results."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    standard: ComplianceStandard
    results: tuple[AiComplianceResult, ...] = ()
    overall_status: ComplianceStatus = ComplianceStatus.PENDING
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    score: float = 0.0
    generated_at: datetime = Field(default_factory=utc_now)


class AiAuditTrail(BaseModel):
    """An audit trail entry recording governance or compliance activity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    action: str
    actor: str = ""
    resource_id: str = ""
    resource_type: str = ""
    details: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=utc_now)


class AiGovernanceConfig(BaseModel):
    """Configuration for the AI Governance subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    auto_enforce: bool = False
    audit_enabled: bool = True
    compliance_check_interval_hours: int = 24
    max_policy_rules: int = 100
    notify_on_violation: bool = True
    notify_on_compliance_failure: bool = True
    metadata: dict[str, str] = {}


class AiBiasCheckResult(BaseModel):
    """Result of an AI bias detection check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    model_id: str = ""
    dataset_id: str = ""
    bias_score: float = 0.0
    threshold: float = 0.1
    biased: bool = False
    dimensions: dict[str, float] = {}
    recommendations: tuple[str, ...] = ()
    checked_at: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = {}


class AiFairnessMetric(BaseModel):
    """A computed fairness metric for an AI model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    model_id: str = ""
    metric_name: str = ""
    value: float = 0.0
    threshold: float = 0.0
    passed: bool = False
    computed_at: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = {}


class AiExplainabilityRecord(BaseModel):
    """An explainability record for an AI model prediction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    model_id: str = ""
    prediction_id: str = ""
    method: str = ""
    explanation: dict[str, Any] = {}
    feature_importance: dict[str, float] = {}
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=utc_now)


class AiGovernanceDashboard(BaseModel):
    """Dashboard snapshot for AI governance overview."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str = ""
    total_policies: int = 0
    active_policies: int = 0
    total_compliance_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    open_reviews: int = 0
    risk_assessments: int = 0
    overall_compliance_score: float = 0.0
    updated_at: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = {}


class AiGovernanceReview(BaseModel):
    """A human review of an AI governance decision or model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str = ""
    resource_type: str = ""
    reviewer: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    comments: str = ""
    decision: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    details: dict[str, Any] = {}


class AiModelRiskAssessment(BaseModel):
    """A risk assessment for an AI model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    model_id: str = ""
    model_name: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0
    dimensions: dict[str, float] = {}
    recommendations: tuple[str, ...] = ()
    assessed_at: datetime = Field(default_factory=utc_now)
    details: dict[str, Any] = {}


__all__ = [
    "AiAuditTrail",
    "AiBiasCheckResult",
    "AiComplianceCheck",
    "AiComplianceReport",
    "AiComplianceRequirement",
    "AiComplianceResult",
    "AiExplainabilityRecord",
    "AiFairnessMetric",
    "AiGovernanceConfig",
    "AiGovernanceDashboard",
    "AiGovernancePolicy",
    "AiGovernanceReview",
    "AiGovernanceRule",
    "AiModelRiskAssessment",
    "ComplianceStandard",
    "ComplianceStatus",
    "PolicyType",
    "ReviewStatus",
    "RiskLevel",
]
