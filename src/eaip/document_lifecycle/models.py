"""Document Lifecycle domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DocumentLifecycleStatus(StrEnum):
    """Status of a document in its lifecycle."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


class DocumentVersionStatus(StrEnum):
    """Status of a document version."""

    DRAFT = "draft"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    REVERTED = "reverted"


class ReviewStatus(StrEnum):
    """Status of a document review."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class DocumentLifecycleActionType(StrEnum):
    """Types of actions that can be performed on a document lifecycle."""

    CREATE = "create"
    UPDATE = "update"
    VERSION = "version"
    STATUS_CHANGE = "status_change"
    APPROVE = "approve"
    REJECT = "reject"
    ARCHIVE = "archive"
    RESTORE = "restore"
    EXPIRE = "expire"
    DELETE = "delete"
    REVIEW = "review"
    REVIEW_REQUEST = "review_request"
    POLICY_APPLY = "policy_apply"
    RETENTION_ENFORCE = "retention_enforce"
    EXPIRY_WARNING = "expiry_warning"


class DocumentLifecycle(BaseModel):
    """Represents a document's lifecycle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    document_id: str
    title: str
    status: DocumentLifecycleStatus = DocumentLifecycleStatus.ACTIVE
    current_version_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    archived_at: datetime | None = None
    expires_at: datetime | None = None


class DocumentVersion(BaseModel):
    """A version of a document within its lifecycle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    lifecycle_id: str
    version: str
    status: DocumentVersionStatus = DocumentVersionStatus.DRAFT
    body: str = ""
    checksum: str = ""
    change_log: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentRevision(BaseModel):
    """A revision within a document version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    version_id: str
    revision_number: int
    diff: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    comment: str = ""


class DocumentLifecycleConfig(BaseModel):
    """Configuration for the document lifecycle subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_versions: int = 50
    enable_versioning: bool = True
    enable_approvals: bool = True
    enable_reviews: bool = True
    enable_retention: bool = True
    enable_expiry: bool = True
    default_expiry_days: int = 365
    retention_period_days: int = 730


class DocumentLifecyclePolicy(BaseModel):
    """A policy that can be applied to document lifecycles."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    rules: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class DocumentLifecycleAction(BaseModel):
    """An action recorded against a document lifecycle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    lifecycle_id: str
    action_type: DocumentLifecycleActionType
    actor: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    performed_at: datetime = Field(default_factory=utc_now)


class DocumentLifecycleStage(BaseModel):
    """A stage in a document approval workflow."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    order: int = 0
    required_approvals: int = 0
    required_reviews: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentLifecycleTransition(BaseModel):
    """A transition between stages in a workflow."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    from_stage: str = ""
    to_stage: str
    conditions: dict[str, Any] = Field(default_factory=dict)
    auto: bool = False


class DocumentRetentionPolicy(BaseModel):
    """A retention policy controlling document expiry and archiving."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    retention_days: int = 730
    action_on_expiry: str = "archive"
    exclude_tags: tuple[str, ...] = Field(default_factory=tuple)
    enabled: bool = True


class DocumentApprovalWorkflow(BaseModel):
    """A workflow defining approval stages and transitions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    stages: tuple[DocumentLifecycleStage, ...] = Field(default_factory=tuple)
    transitions: tuple[DocumentLifecycleTransition, ...] = Field(default_factory=tuple)
    required_approvers: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentReview(BaseModel):
    """A review record for a document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    lifecycle_id: str
    reviewer: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    comments: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class DocumentExpiryConfig(BaseModel):
    """Expiry configuration for a document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    lifecycle_id: str
    expires_at: datetime
    warning_days_before: int = 30
    auto_archive: bool = True
    notified: bool = False


class DocumentLifecycleReport(BaseModel):
    """A report on document lifecycle status."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    generated_at: datetime = Field(default_factory=utc_now)
    total_documents: int = 0
    active_count: int = 0
    archived_count: int = 0
    expired_count: int = 0
    pending_review_count: int = 0
    pending_approval_count: int = 0
    expiring_soon_count: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


class DocumentAuditEntry(BaseModel):
    """An audit log entry for a document lifecycle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    lifecycle_id: str
    action: str = ""
    actor: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    changes: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "DocumentApprovalWorkflow",
    "DocumentAuditEntry",
    "DocumentExpiryConfig",
    "DocumentLifecycle",
    "DocumentLifecycleAction",
    "DocumentLifecycleActionType",
    "DocumentLifecycleConfig",
    "DocumentLifecyclePolicy",
    "DocumentLifecycleReport",
    "DocumentLifecycleStage",
    "DocumentLifecycleStatus",
    "DocumentLifecycleTransition",
    "DocumentRetentionPolicy",
    "DocumentReview",
    "DocumentRevision",
    "DocumentVersion",
    "DocumentVersionStatus",
    "ReviewStatus",
]
