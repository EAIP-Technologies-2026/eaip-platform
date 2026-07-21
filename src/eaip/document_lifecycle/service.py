"""Document Lifecycle Service — lifecycle management, versioning, approvals, reviews, retention."""

from __future__ import annotations

import hashlib
from typing import Any

from eaip.document_lifecycle.exceptions import (
    DocumentApprovalError,
    DocumentArchiveError,
    DocumentExpiryError,
    DocumentNotFoundError,
    DocumentRetentionError,
    DocumentReviewError,
    DocumentStatusError,
    DocumentVersionError,
)
from eaip.document_lifecycle.models import (
    DocumentApprovalWorkflow,
    DocumentAuditEntry,
    DocumentExpiryConfig,
    DocumentLifecycle,
    DocumentLifecycleAction,
    DocumentLifecycleActionType,
    DocumentLifecycleConfig,
    DocumentLifecyclePolicy,
    DocumentLifecycleReport,
    DocumentLifecycleStatus,
    DocumentRetentionPolicy,
    DocumentReview,
    DocumentRevision,
    DocumentVersion,
    ReviewStatus,
)
from eaip.shared.time import utc_now


class DocumentLifecycleService:
    """Service for managing document lifecycles, versions, approvals, reviews, and retention."""

    def __init__(self, config: DocumentLifecycleConfig | None = None) -> None:
        self._config = config or DocumentLifecycleConfig()
        self._lifecycles: dict[str, DocumentLifecycle] = {}
        self._versions: dict[str, dict[str, DocumentVersion]] = {}
        self._revisions: dict[str, list[DocumentRevision]] = {}
        self._reviews: dict[str, list[DocumentReview]] = {}
        self._workflows: dict[str, DocumentApprovalWorkflow] = {}
        self._policies: dict[str, DocumentLifecyclePolicy] = {}
        self._retention_policies: dict[str, DocumentRetentionPolicy] = {}
        self._expiry_configs: dict[str, DocumentExpiryConfig] = {}
        self._actions: dict[str, list[DocumentLifecycleAction]] = {}
        self._audit_entries: dict[str, list[DocumentAuditEntry]] = {}

    @property
    def config(self) -> DocumentLifecycleConfig:
        """Return the service configuration."""
        return self._config

    def create_document(
        self,
        document_id: str,
        title: str,
        author: str = "",
        **metadata: Any,
    ) -> DocumentLifecycle:
        """Create a new document lifecycle."""
        if document_id in self._lifecycles:
            raise DocumentVersionError(document_id, "already exists")
        lifecycle = DocumentLifecycle(
            id=document_id,
            document_id=document_id,
            title=title,
            metadata=metadata,
        )
        self._lifecycles[document_id] = lifecycle
        self._versions[document_id] = {}
        self._reviews[document_id] = []
        self._actions[document_id] = []
        self._audit_entries[document_id] = []
        self._record_action(document_id, DocumentLifecycleActionType.CREATE, actor=author)
        return lifecycle

    def get_document(self, document_id: str) -> DocumentLifecycle:
        """Get a document lifecycle by ID."""
        if document_id not in self._lifecycles:
            raise DocumentNotFoundError(document_id)
        return self._lifecycles[document_id]

    def update_document(
        self,
        document_id: str,
        title: str | None = None,
        author: str = "",
        **metadata: Any,
    ) -> DocumentLifecycle:
        """Update a document's title and/or metadata."""
        lifecycle = self.get_document(document_id)
        if lifecycle.status is not DocumentLifecycleStatus.ACTIVE:
            raise DocumentStatusError(document_id, lifecycle.status.value, "update")
        updated = DocumentLifecycle(
            id=lifecycle.id,
            document_id=lifecycle.document_id,
            title=title if title is not None else lifecycle.title,
            status=lifecycle.status,
            current_version_id=lifecycle.current_version_id,
            metadata={**lifecycle.metadata, **metadata},
            created_at=lifecycle.created_at,
            updated_at=utc_now(),
            archived_at=lifecycle.archived_at,
            expires_at=lifecycle.expires_at,
        )
        self._lifecycles[document_id] = updated
        self._record_action(document_id, DocumentLifecycleActionType.UPDATE, actor=author)
        return updated

    def create_version(
        self,
        document_id: str,
        version_id: str,
        version: str,
        body: str = "",
        change_log: str = "",
        author: str = "",
    ) -> DocumentVersion:
        """Create a new version for a document."""
        lifecycle = self.get_document(document_id)
        if not self._config.enable_versioning:
            raise DocumentVersionError(document_id, "versioning is disabled")
        versions = self._versions[document_id]
        if version_id in versions:
            raise DocumentVersionError(document_id, f"version {version_id!r} already exists")
        checksum = hashlib.sha256(body.encode()).hexdigest() if body else ""
        doc_version = DocumentVersion(
            id=version_id,
            lifecycle_id=document_id,
            version=version,
            body=body,
            checksum=checksum,
            change_log=change_log,
            author=author,
        )
        versions[version_id] = doc_version
        updated = DocumentLifecycle(
            id=lifecycle.id,
            document_id=lifecycle.document_id,
            title=lifecycle.title,
            status=lifecycle.status,
            current_version_id=version_id,
            metadata=lifecycle.metadata,
            created_at=lifecycle.created_at,
            updated_at=utc_now(),
            archived_at=lifecycle.archived_at,
            expires_at=lifecycle.expires_at,
        )
        self._lifecycles[document_id] = updated
        self._record_action(document_id, DocumentLifecycleActionType.VERSION, actor=author)
        return doc_version

    def get_version(self, document_id: str, version_id: str) -> DocumentVersion:
        """Get a specific version of a document."""
        self.get_document(document_id)
        versions = self._versions.get(document_id, {})
        if version_id not in versions:
            raise DocumentVersionError(document_id, f"version {version_id!r} not found")
        return versions[version_id]

    def list_versions(self, document_id: str) -> tuple[DocumentVersion, ...]:
        """List all versions of a document."""
        self.get_document(document_id)
        return tuple(self._versions.get(document_id, {}).values())

    def change_status(
        self,
        document_id: str,
        new_status: DocumentLifecycleStatus,
        actor: str = "",
    ) -> DocumentLifecycle:
        """Change the lifecycle status of a document."""
        lifecycle = self.get_document(document_id)
        old_status = lifecycle.status
        if old_status == new_status:
            return lifecycle
        valid_transitions: dict[DocumentLifecycleStatus, tuple[DocumentLifecycleStatus, ...]] = {
            DocumentLifecycleStatus.ACTIVE: (
                DocumentLifecycleStatus.ARCHIVED,
                DocumentLifecycleStatus.EXPIRED,
            ),
            DocumentLifecycleStatus.ARCHIVED: (
                DocumentLifecycleStatus.ACTIVE,
                DocumentLifecycleStatus.DELETED,
            ),
            DocumentLifecycleStatus.EXPIRED: (
                DocumentLifecycleStatus.ARCHIVED,
                DocumentLifecycleStatus.DELETED,
            ),
            DocumentLifecycleStatus.DELETED: (),
        }
        allowed = valid_transitions.get(old_status, ())
        if new_status not in allowed:
            raise DocumentStatusError(document_id, old_status.value, new_status.value)
        archived_at = (
            utc_now() if new_status == DocumentLifecycleStatus.ARCHIVED else lifecycle.archived_at
        )
        updated = DocumentLifecycle(
            id=lifecycle.id,
            document_id=lifecycle.document_id,
            title=lifecycle.title,
            status=new_status,
            current_version_id=lifecycle.current_version_id,
            metadata=lifecycle.metadata,
            created_at=lifecycle.created_at,
            updated_at=utc_now(),
            archived_at=archived_at,
            expires_at=lifecycle.expires_at,
        )
        self._lifecycles[document_id] = updated
        self._record_action(
            document_id,
            DocumentLifecycleActionType.STATUS_CHANGE,
            actor=actor,
        )
        return updated

    def archive_document(
        self, document_id: str, actor: str = "", reason: str = ""
    ) -> DocumentLifecycle:
        """Archive a document."""
        result = self.change_status(document_id, DocumentLifecycleStatus.ARCHIVED, actor=actor)
        self._record_action(
            document_id,
            DocumentLifecycleActionType.ARCHIVE,
            actor=actor,
            details={"reason": reason},
        )
        return result

    def restore_document(
        self, document_id: str, actor: str = "", reason: str = ""
    ) -> DocumentLifecycle:
        """Restore an archived document."""
        lifecycle = self.get_document(document_id)
        if lifecycle.status != DocumentLifecycleStatus.ARCHIVED:
            raise DocumentArchiveError(document_id, "document is not archived")
        result = self.change_status(document_id, DocumentLifecycleStatus.ACTIVE, actor=actor)
        self._record_action(
            document_id,
            DocumentLifecycleActionType.RESTORE,
            actor=actor,
            details={"reason": reason},
        )
        return result

    def delete_document(self, document_id: str, actor: str = "", reason: str = "") -> None:
        """Delete a document."""
        lifecycle = self.get_document(document_id)
        if lifecycle.status == DocumentLifecycleStatus.DELETED:
            raise DocumentArchiveError(document_id, "document is already deleted")
        self.change_status(document_id, DocumentLifecycleStatus.DELETED, actor=actor)
        self._record_action(
            document_id,
            DocumentLifecycleActionType.DELETE,
            actor=actor,
            details={"reason": reason},
        )

    def expire_document(self, document_id: str, expiry_config_id: str = "") -> DocumentLifecycle:
        """Expire a document."""
        lifecycle = self.get_document(document_id)
        if lifecycle.status in (
            DocumentLifecycleStatus.EXPIRED,
            DocumentLifecycleStatus.DELETED,
        ):
            raise DocumentExpiryError(document_id, "document is already expired or deleted")
        result = self.change_status(document_id, DocumentLifecycleStatus.EXPIRED, actor="system")
        self._record_action(
            document_id,
            DocumentLifecycleActionType.EXPIRE,
            actor="system",
            details={"expiry_config_id": expiry_config_id},
        )
        return result

    def request_review(
        self,
        document_id: str,
        review_id: str,
        reviewer: str,
        requested_by: str = "",
    ) -> DocumentReview:
        """Request a review for a document."""
        self.get_document(document_id)
        review = DocumentReview(
            id=review_id,
            lifecycle_id=document_id,
            reviewer=reviewer,
            status=ReviewStatus.PENDING,
        )
        reviews = self._reviews.setdefault(document_id, [])
        reviews.append(review)
        self._record_action(
            document_id,
            DocumentLifecycleActionType.REVIEW_REQUEST,
            actor=requested_by,
            details={"review_id": review_id, "reviewer": reviewer},
        )
        return review

    def submit_review(
        self,
        document_id: str,
        review_id: str,
        status: ReviewStatus,
        comments: str = "",
        reviewer: str = "",
    ) -> DocumentReview:
        """Submit a review for a document."""
        self.get_document(document_id)
        reviews = self._reviews.get(document_id, [])
        for i, r in enumerate(reviews):
            if r.id == review_id:
                updated = DocumentReview(
                    id=r.id,
                    lifecycle_id=r.lifecycle_id,
                    reviewer=reviewer or r.reviewer,
                    status=status,
                    comments=comments,
                    created_at=r.created_at,
                    completed_at=utc_now(),
                )
                reviews[i] = updated
                self._record_action(
                    document_id,
                    DocumentLifecycleActionType.REVIEW,
                    actor=reviewer,
                    details={
                        "review_id": review_id,
                        "status": status.value,
                    },
                )
                return updated
        raise DocumentReviewError(document_id, f"review {review_id!r} not found")

    def approve_document(
        self,
        document_id: str,
        workflow_id: str,
        approver: str,
        comment: str = "",
    ) -> DocumentLifecycle:
        """Approve a document through a workflow."""
        lifecycle = self.get_document(document_id)
        if workflow_id not in self._workflows:
            raise DocumentApprovalError(document_id, f"workflow {workflow_id!r} not found")
        if lifecycle.status != DocumentLifecycleStatus.ACTIVE:
            raise DocumentStatusError(document_id, lifecycle.status.value, "approve")
        self._record_action(
            document_id,
            DocumentLifecycleActionType.APPROVE,
            actor=approver,
            details={"workflow_id": workflow_id, "comment": comment},
        )
        return lifecycle

    def reject_document(
        self,
        document_id: str,
        workflow_id: str,
        reviewer: str,
        reason: str = "",
    ) -> DocumentLifecycle:
        """Reject a document through a workflow."""
        lifecycle = self.get_document(document_id)
        if workflow_id not in self._workflows:
            raise DocumentApprovalError(document_id, f"workflow {workflow_id!r} not found")
        self._record_action(
            document_id,
            DocumentLifecycleActionType.REJECT,
            actor=reviewer,
            details={"workflow_id": workflow_id, "reason": reason},
        )
        return lifecycle

    def create_policy(self, policy: DocumentLifecyclePolicy) -> DocumentLifecyclePolicy:
        """Register a lifecycle policy."""
        self._policies[policy.id] = policy
        return policy

    def apply_policy(self, document_id: str, policy_id: str) -> DocumentLifecycle:
        """Apply a lifecycle policy to a document."""
        self.get_document(document_id)
        if policy_id not in self._policies:
            raise DocumentRetentionError(document_id, f"policy {policy_id!r} not found")
        self._record_action(
            document_id,
            DocumentLifecycleActionType.POLICY_APPLY,
            actor="system",
            details={"policy_id": policy_id},
        )
        return self._lifecycles[document_id]

    def create_retention_policy(self, policy: DocumentRetentionPolicy) -> DocumentRetentionPolicy:
        """Register a retention policy."""
        self._retention_policies[policy.id] = policy
        return policy

    def enforce_retention(self, document_id: str, retention_policy_id: str) -> DocumentLifecycle:
        """Enforce a retention policy on a document."""
        self.get_document(document_id)
        if retention_policy_id not in self._retention_policies:
            raise DocumentRetentionError(
                document_id,
                f"retention policy {retention_policy_id!r} not found",
            )
        policy = self._retention_policies[retention_policy_id]
        action = policy.action_on_expiry
        if action == "archive":
            self.archive_document(
                document_id,
                actor="system",
                reason=f"retention policy {policy.name}",
            )
        elif action == "delete":
            self.delete_document(
                document_id,
                actor="system",
                reason=f"retention policy {policy.name}",
            )
        self._record_action(
            document_id,
            DocumentLifecycleActionType.RETENTION_ENFORCE,
            actor="system",
            details={
                "retention_policy_id": retention_policy_id,
                "action": action,
            },
        )
        return self._lifecycles[document_id]

    def create_workflow(self, workflow: DocumentApprovalWorkflow) -> DocumentApprovalWorkflow:
        """Register an approval workflow."""
        self._workflows[workflow.id] = workflow
        return workflow

    def set_expiry(self, document_id: str, config: DocumentExpiryConfig) -> DocumentExpiryConfig:
        """Set expiry configuration for a document."""
        self.get_document(document_id)
        self._expiry_configs[config.id] = config
        updated = DocumentLifecycle(
            id=self._lifecycles[document_id].id,
            document_id=document_id,
            title=self._lifecycles[document_id].title,
            status=self._lifecycles[document_id].status,
            current_version_id=self._lifecycles[document_id].current_version_id,
            metadata=self._lifecycles[document_id].metadata,
            created_at=self._lifecycles[document_id].created_at,
            updated_at=utc_now(),
            archived_at=self._lifecycles[document_id].archived_at,
            expires_at=config.expires_at,
        )
        self._lifecycles[document_id] = updated
        return config

    def check_expiry_warnings(self) -> list[DocumentExpiryConfig]:
        """Check for documents that need expiry warnings."""
        now = utc_now()
        warnings: list[DocumentExpiryConfig] = []
        for config in self._expiry_configs.values():
            if config.notified:
                continue
            remaining = (config.expires_at - now).days
            if 0 < remaining <= config.warning_days_before:
                warnings.append(config)
        return warnings

    def get_report(self) -> DocumentLifecycleReport:
        """Generate a lifecycle status report."""
        all_lifecycles = list(self._lifecycles.values())
        total = len(all_lifecycles)
        active = sum(1 for lc in all_lifecycles if lc.status == DocumentLifecycleStatus.ACTIVE)
        archived = sum(1 for lc in all_lifecycles if lc.status == DocumentLifecycleStatus.ARCHIVED)
        expired = sum(1 for lc in all_lifecycles if lc.status == DocumentLifecycleStatus.EXPIRED)
        pending_reviews = sum(
            1
            for reviews in self._reviews.values()
            for r in reviews
            if r.status == ReviewStatus.PENDING
        )
        now = utc_now()
        expiring_soon = sum(
            1
            for ec in self._expiry_configs.values()
            if not ec.notified and 0 < (ec.expires_at - now).days <= ec.warning_days_before
        )
        return DocumentLifecycleReport(
            id="report",
            total_documents=total,
            active_count=active,
            archived_count=archived,
            expired_count=expired,
            pending_review_count=pending_reviews,
            pending_approval_count=0,
            expiring_soon_count=expiring_soon,
        )

    def get_actions(self, document_id: str) -> tuple[DocumentLifecycleAction, ...]:
        """Get all actions recorded for a document."""
        self.get_document(document_id)
        return tuple(self._actions.get(document_id, []))

    def get_audit_trail(self, document_id: str) -> tuple[DocumentAuditEntry, ...]:
        """Get the audit trail for a document."""
        self.get_document(document_id)
        return tuple(self._audit_entries.get(document_id, []))

    def _record_action(
        self,
        document_id: str,
        action_type: DocumentLifecycleActionType,
        actor: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        action = DocumentLifecycleAction(
            id=f"{document_id}-{action_type.value}-{utc_now().isoformat()}",
            lifecycle_id=document_id,
            action_type=action_type,
            actor=actor,
            details=details or {},
        )
        self._actions.setdefault(document_id, []).append(action)
        audit = DocumentAuditEntry(
            id=action.id,
            lifecycle_id=document_id,
            action=action_type.value,
            actor=actor,
            changes=details or {},
        )
        self._audit_entries.setdefault(document_id, []).append(audit)


__all__ = [
    "DocumentLifecycleService",
]
