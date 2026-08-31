"""Knowledge Governance models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class GovernanceScope(StrEnum):
    """Scope of governance policy application."""

    GLOBAL = "global"
    COLLECTION = "collection"
    DOCUMENT = "document"
    DEPARTMENT = "department"


class KnowledgeRetentionAction(StrEnum):
    """Action to take when a retention rule is triggered."""

    ARCHIVE = "archive"
    DELETE = "delete"
    NOTIFY = "notify"


class KnowledgeClassificationLevel(StrEnum):
    """Classification levels for knowledge resources."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    CRITICAL = "critical"


class KnowledgeSourceStatus(StrEnum):
    """Status of a knowledge source validation."""

    PENDING = "pending"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"


class KnowledgeStewardshipRole(StrEnum):
    """Roles for knowledge stewardship assignments."""

    OWNER = "owner"
    STEWARD = "steward"
    REVIEWER = "reviewer"
    CONTRIBUTOR = "contributor"


class KnowledgeGovernanceRule(BaseModel):
    """A single rule within a governance policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    actions: tuple[str, ...] = ()
    effect: str = "allow"
    enabled: bool = True
    priority: int = 0
    conditions: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGovernancePolicy(BaseModel):
    """A policy governing knowledge access and usage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    scope: GovernanceScope = GovernanceScope.GLOBAL
    rules: tuple[KnowledgeGovernanceRule, ...] = ()
    enabled: bool = True
    tags: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgeQualityMetric(BaseModel):
    """A metric tracked for knowledge quality."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    value: float = 0.0
    threshold: float = 0.0
    passed: bool = True
    timestamp: datetime = Field(default_factory=utc_now)


class KnowledgeQualityCheck(BaseModel):
    """A quality check performed on knowledge resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    resource_id: str = ""
    resource_type: str = ""
    metrics: tuple[KnowledgeQualityMetric, ...] = ()
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    status: str = "pending"


class KnowledgeQualityResult(BaseModel):
    """Result of a knowledge quality check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    check_id: str
    resource_id: str
    resource_type: str
    metrics: tuple[KnowledgeQualityMetric, ...] = ()
    overall_score: float = 0.0
    passed: bool = True
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=utc_now)


class KnowledgeQualityScore(BaseModel):
    """Aggregated quality score for a knowledge resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: str
    score: float = 0.0
    metric_count: int = 0
    passed_count: int = 0
    computed_at: datetime = Field(default_factory=utc_now)


class KnowledgeAuditTrail(BaseModel):
    """An audit trail entry for knowledge governance actions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    action: str
    actor: str = ""
    resource_id: str = ""
    resource_type: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class KnowledgeGovernanceReport(BaseModel):
    """A report summarising knowledge governance activities."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    report_type: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)


class KnowledgeRetentionRule(BaseModel):
    """A rule defining retention behaviour for knowledge resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    resource_type: str = ""
    max_age_days: int = 365
    action: KnowledgeRetentionAction = KnowledgeRetentionAction.ARCHIVE
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgeClassificationPolicy(BaseModel):
    """A policy governing classification of knowledge resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    default_level: KnowledgeClassificationLevel = KnowledgeClassificationLevel.INTERNAL
    allowed_levels: tuple[KnowledgeClassificationLevel, ...] = ()
    auto_classify: bool = False
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgeSourceValidation(BaseModel):
    """Validation record for a knowledge source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_id: str
    source_type: str = ""
    status: KnowledgeSourceStatus = KnowledgeSourceStatus.PENDING
    validated_by: str = ""
    validation_notes: str = ""
    validated_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeGovernanceDashboard(BaseModel):
    """Dashboard snapshot of knowledge governance metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str = "Knowledge Governance Dashboard"
    total_policies: int = 0
    active_policies: int = 0
    total_quality_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    audit_entries: int = 0
    retention_rules: int = 0
    classification_policies: int = 0
    source_validations: int = 0
    stewardship_assignments: int = 0
    overall_quality_score: float = 0.0
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgeStewardshipAssignment(BaseModel):
    """Assignment of a stewardship role to a user for a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    resource_type: str = ""
    user_id: str
    role: KnowledgeStewardshipRole = KnowledgeStewardshipRole.STEWARD
    assigned_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None


class KnowledgeGovernanceConfig(BaseModel):
    """Configuration for the knowledge governance subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    policies_enabled: bool = True
    quality_checks_enabled: bool = True
    audit_enabled: bool = True
    retention_enabled: bool = True
    classification_enabled: bool = True
    source_validation_enabled: bool = True
    stewardship_enabled: bool = True
    dashboard_enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "GovernanceScope",
    "KnowledgeAuditTrail",
    "KnowledgeClassificationLevel",
    "KnowledgeClassificationPolicy",
    "KnowledgeGovernanceConfig",
    "KnowledgeGovernanceDashboard",
    "KnowledgeGovernancePolicy",
    "KnowledgeGovernanceReport",
    "KnowledgeGovernanceRule",
    "KnowledgeQualityCheck",
    "KnowledgeQualityMetric",
    "KnowledgeQualityResult",
    "KnowledgeQualityScore",
    "KnowledgeRetentionAction",
    "KnowledgeRetentionRule",
    "KnowledgeSourceStatus",
    "KnowledgeSourceValidation",
    "KnowledgeStewardshipAssignment",
    "KnowledgeStewardshipRole",
]
