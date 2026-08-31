"""Audit domain models — events, policies, classification, retention, legal holds, compliance, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActorType(StrEnum):
    USER = "user"
    SYSTEM = "system"
    AGENT = "agent"
    WORKFLOW = "workflow"


class ClassificationLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class RetentionAction(StrEnum):
    ARCHIVE = "archive"
    DELETE = "delete"
    ANONYMIZE = "anonymize"


class LegalHoldStatus(StrEnum):
    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class ComplianceStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    IN_PROGRESS = "in_progress"
    NOT_APPLICABLE = "not_applicable"


class AuditLevel(StrEnum):
    BASIC = "basic"
    DETAILED = "detailed"
    FULL = "full"


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    event_type: str
    actor_id: str
    actor_type: ActorType
    action: str
    resource_type: str
    resource_id: str
    target_id: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    change_summary: dict[str, Any] = Field(default_factory=dict)
    old_value: str | None = None
    new_value: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    correlation_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    session_id: str = ""
    severity: Severity = Severity.INFO
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    event_types: tuple[str, ...] = Field(default=())
    retention_days: int = 90
    storage_backend: str = "memory"
    encryption_enabled: bool = True
    notify_on_events: tuple[str, ...] = Field(default=())
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataClassification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    level: ClassificationLevel
    rules: tuple[str, ...] = Field(default=())
    retention_days: int = 90
    handling_instructions: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetentionRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    data_type: str
    retention_period_days: int
    action_on_expiry: RetentionAction
    legal_hold_ids: tuple[str, ...] = Field(default=())
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class LegalHold(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    reason: str
    affected_data_types: tuple[str, ...] = Field(default=())
    affected_resources: tuple[str, ...] = Field(default=())
    start_date: datetime = Field(default_factory=utc_now)
    end_date: datetime | None = None
    status: LegalHoldStatus = LegalHoldStatus.ACTIVE
    created_by: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComplianceReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    framework: str
    status: ComplianceStatus
    findings: tuple[dict[str, Any], ...] = Field(default=())
    score: float = 0.0
    generated_at: datetime = Field(default_factory=utc_now)
    period_start: datetime | None = None
    period_end: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_immutable_log: bool = True
    retention_default_days: int = 90
    encryption_enabled: bool = True
    max_batch_size: int = 100
    enable_legal_hold: bool = True
    audit_level: AuditLevel = AuditLevel.DETAILED


__all__ = [
    "ActorType",
    "AuditConfig",
    "AuditEvent",
    "AuditLevel",
    "AuditPolicy",
    "ClassificationLevel",
    "ComplianceReport",
    "ComplianceStatus",
    "DataClassification",
    "LegalHold",
    "LegalHoldStatus",
    "RetentionAction",
    "RetentionRule",
    "Severity",
]
