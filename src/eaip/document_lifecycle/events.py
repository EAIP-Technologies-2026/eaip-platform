"""Domain events for the document lifecycle."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class DocumentCreated(DomainEvent):
    """Published when a document lifecycle is created."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.created"
    document_id: str = ""
    title: str = ""
    author: str = ""


class DocumentUpdated(DomainEvent):
    """Published when a document is updated."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.updated"
    document_id: str = ""
    title: str = ""
    version: str = ""
    author: str = ""


class DocumentVersioned(DomainEvent):
    """Published when a new document version is created."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.versioned"
    document_id: str = ""
    version_id: str = ""
    version: str = ""
    change_log: str = ""
    author: str = ""


class DocumentStatusChanged(DomainEvent):
    """Published when a document's lifecycle status changes."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.status_changed"
    document_id: str = ""
    from_status: str = ""
    to_status: str = ""
    actor: str = ""


class DocumentApproved(DomainEvent):
    """Published when a document is approved."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.approved"
    document_id: str = ""
    workflow_id: str = ""
    approver: str = ""
    comment: str = ""


class DocumentRejected(DomainEvent):
    """Published when a document is rejected."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.rejected"
    document_id: str = ""
    workflow_id: str = ""
    reviewer: str = ""
    reason: str = ""


class DocumentArchived(DomainEvent):
    """Published when a document is archived."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.archived"
    document_id: str = ""
    actor: str = ""
    reason: str = ""


class DocumentRestored(DomainEvent):
    """Published when a document is restored from archive."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.restored"
    document_id: str = ""
    actor: str = ""
    reason: str = ""


class DocumentExpired(DomainEvent):
    """Published when a document expires."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.expired"
    document_id: str = ""
    expiry_config_id: str = ""


class DocumentDeleted(DomainEvent):
    """Published when a document is deleted."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.deleted"
    document_id: str = ""
    actor: str = ""
    reason: str = ""


class DocumentReviewed(DomainEvent):
    """Published when a document review is submitted."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.reviewed"
    document_id: str = ""
    review_id: str = ""
    reviewer: str = ""
    comment: str = ""


class DocumentReviewRequested(DomainEvent):
    """Published when a document review is requested."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.review_requested"
    document_id: str = ""
    review_id: str = ""
    requested_by: str = ""
    assignees: tuple[str, ...] = ()


class DocumentReviewCompleted(DomainEvent):
    """Published when a document review is completed."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.review_completed"
    document_id: str = ""
    review_id: str = ""
    status: str = ""


class DocumentLifecyclePolicyApplied(DomainEvent):
    """Published when a lifecycle policy is applied to a document."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.policy_applied"
    document_id: str = ""
    policy_id: str = ""
    policy_name: str = ""


class DocumentRetentionPolicyEnforced(DomainEvent):
    """Published when a retention policy is enforced on a document."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.retention_enforced"
    document_id: str = ""
    retention_policy_id: str = ""
    action_taken: str = ""


class DocumentExpiryWarningSent(DomainEvent):
    """Published when an expiry warning is sent for a document."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.expiry_warning"
    document_id: str = ""
    expires_at: str = ""
    days_remaining: int = 0


class DocumentLifecycleReportGenerated(DomainEvent):
    """Published when a lifecycle report is generated."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.report_generated"
    report_id: str = ""
    total_documents: int = 0


class DocumentAuditLogged(DomainEvent):
    """Published when an audit entry is logged."""

    event_type: ClassVar[str] = "eaip.document_lifecycle.audit_logged"
    audit_id: str = ""
    lifecycle_id: str = ""
    action: str = ""
    actor: str = ""


DocumentLifecycleEvent = (
    DocumentApproved
    | DocumentArchived
    | DocumentAuditLogged
    | DocumentCreated
    | DocumentDeleted
    | DocumentExpired
    | DocumentExpiryWarningSent
    | DocumentLifecyclePolicyApplied
    | DocumentLifecycleReportGenerated
    | DocumentRejected
    | DocumentRestored
    | DocumentRetentionPolicyEnforced
    | DocumentReviewCompleted
    | DocumentReviewRequested
    | DocumentReviewed
    | DocumentStatusChanged
    | DocumentUpdated
    | DocumentVersioned
)


__all__ = [
    "DocumentApproved",
    "DocumentArchived",
    "DocumentAuditLogged",
    "DocumentCreated",
    "DocumentDeleted",
    "DocumentExpired",
    "DocumentExpiryWarningSent",
    "DocumentLifecycleEvent",
    "DocumentLifecyclePolicyApplied",
    "DocumentLifecycleReportGenerated",
    "DocumentRejected",
    "DocumentRestored",
    "DocumentRetentionPolicyEnforced",
    "DocumentReviewCompleted",
    "DocumentReviewRequested",
    "DocumentReviewed",
    "DocumentStatusChanged",
    "DocumentUpdated",
    "DocumentVersioned",
]
