"""Tests for the Document Lifecycle package."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

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
    DocumentExpiryConfig,
    DocumentLifecycleActionType,
    DocumentLifecycleConfig,
    DocumentLifecyclePolicy,
    DocumentLifecycleStatus,
    DocumentRetentionPolicy,
    ReviewStatus,
)
from eaip.document_lifecycle.service import DocumentLifecycleService


@pytest.fixture
def service() -> DocumentLifecycleService:
    return DocumentLifecycleService()


@pytest.fixture
def populated_service(
    service: DocumentLifecycleService,
) -> DocumentLifecycleService:
    service.create_document("doc-1", "Test Document", author="alice")
    service.create_document("doc-2", "Another Document", author="bob")
    return service


class TestDocumentLifecycleCreate:
    def test_create_document(self, service: DocumentLifecycleService) -> None:
        doc = service.create_document("doc-1", "Test", author="alice")
        assert doc.id == "doc-1"
        assert doc.title == "Test"
        assert doc.status == DocumentLifecycleStatus.ACTIVE

    def test_create_duplicate_raises(self, service: DocumentLifecycleService) -> None:
        service.create_document("doc-1", "Test")
        with pytest.raises(DocumentVersionError, match="already exists"):
            service.create_document("doc-1", "Test")

    def test_create_with_metadata(self, service: DocumentLifecycleService) -> None:
        doc = service.create_document("doc-1", "Test", category="guide", priority="high")
        assert doc.metadata["category"] == "guide"
        assert doc.metadata["priority"] == "high"


class TestDocumentLifecycleGet:
    def test_get_existing(self, populated_service: DocumentLifecycleService) -> None:
        doc = populated_service.get_document("doc-1")
        assert doc.document_id == "doc-1"

    def test_get_missing_raises(self, service: DocumentLifecycleService) -> None:
        with pytest.raises(DocumentNotFoundError):
            service.get_document("nonexistent")


class TestDocumentLifecycleUpdate:
    def test_update_title(self, populated_service: DocumentLifecycleService) -> None:
        updated = populated_service.update_document("doc-1", title="Updated Title", author="alice")
        assert updated.title == "Updated Title"

    def test_update_metadata(self, populated_service: DocumentLifecycleService) -> None:
        updated = populated_service.update_document("doc-1", version="2.0")
        assert updated.metadata["version"] == "2.0"

    def test_update_archived_raises(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.archive_document("doc-1", actor="alice")
        with pytest.raises(DocumentStatusError):
            populated_service.update_document("doc-1", title="New")


class TestDocumentLifecycleVersioning:
    def test_create_version(self, populated_service: DocumentLifecycleService) -> None:
        v = populated_service.create_version("doc-1", "v1", "1.0.0", body="content", author="alice")
        assert v.version == "1.0.0"
        assert v.checksum

    def test_get_version(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.create_version("doc-1", "v1", "1.0.0", body="content")
        v = populated_service.get_version("doc-1", "v1")
        assert v.id == "v1"

    def test_get_missing_version_raises(self, populated_service: DocumentLifecycleService) -> None:
        with pytest.raises(DocumentVersionError):
            populated_service.get_version("doc-1", "nonexistent")

    def test_list_versions(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.create_version("doc-1", "v1", "1.0.0")
        populated_service.create_version("doc-1", "v2", "2.0.0")
        versions = populated_service.list_versions("doc-1")
        assert len(versions) == 2

    def test_versioning_disabled(self) -> None:
        cfg = DocumentLifecycleConfig(enable_versioning=False)
        svc = DocumentLifecycleService(config=cfg)
        svc.create_document("doc-1", "Test")
        with pytest.raises(DocumentVersionError, match="versioning is disabled"):
            svc.create_version("doc-1", "v1", "1.0.0")

    def test_duplicate_version_raises(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.create_version("doc-1", "v1", "1.0.0")
        with pytest.raises(DocumentVersionError, match="already exists"):
            populated_service.create_version("doc-1", "v1", "2.0.0")


class TestDocumentLifecycleStatus:
    def test_archive_document(self, populated_service: DocumentLifecycleService) -> None:
        result = populated_service.archive_document("doc-1", actor="alice", reason="obsolete")
        assert result.status == DocumentLifecycleStatus.ARCHIVED

    def test_restore_document(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.archive_document("doc-1")
        result = populated_service.restore_document("doc-1", actor="alice")
        assert result.status == DocumentLifecycleStatus.ACTIVE

    def test_restore_non_archived_raises(self, populated_service: DocumentLifecycleService) -> None:
        with pytest.raises(DocumentArchiveError, match="not archived"):
            populated_service.restore_document("doc-1")

    def test_delete_document(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.delete_document("doc-1", actor="alice", reason="cleanup")
        doc = populated_service.get_document("doc-1")
        assert doc.status == DocumentLifecycleStatus.DELETED

    def test_delete_twice_raises(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.delete_document("doc-1")
        with pytest.raises(DocumentArchiveError, match="already deleted"):
            populated_service.delete_document("doc-1")

    def test_expire_document(self, populated_service: DocumentLifecycleService) -> None:
        result = populated_service.expire_document("doc-1")
        assert result.status == DocumentLifecycleStatus.EXPIRED

    def test_invalid_status_transition(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.delete_document("doc-1")
        with pytest.raises(DocumentStatusError):
            populated_service.change_status("doc-1", DocumentLifecycleStatus.ACTIVE)

    def test_status_change_same_status(self, populated_service: DocumentLifecycleService) -> None:
        result = populated_service.change_status("doc-1", DocumentLifecycleStatus.ACTIVE)
        assert result.status == DocumentLifecycleStatus.ACTIVE

    def test_expire_already_expired_raises(
        self, populated_service: DocumentLifecycleService
    ) -> None:
        populated_service.expire_document("doc-1")
        with pytest.raises(DocumentExpiryError, match="already expired"):
            populated_service.expire_document("doc-1")


class TestDocumentLifecycleReview:
    def test_request_review(self, populated_service: DocumentLifecycleService) -> None:
        review = populated_service.request_review(
            "doc-1", "rev-1", reviewer="bob", requested_by="alice"
        )
        assert review.status == ReviewStatus.PENDING
        assert review.reviewer == "bob"

    def test_submit_review(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.request_review("doc-1", "rev-1", reviewer="bob")
        result = populated_service.submit_review(
            "doc-1",
            "rev-1",
            ReviewStatus.APPROVED,
            comments="Looks good",
            reviewer="bob",
        )
        assert result.status == ReviewStatus.APPROVED
        assert result.completed_at is not None

    def test_submit_missing_review_raises(
        self, populated_service: DocumentLifecycleService
    ) -> None:
        with pytest.raises(DocumentReviewError, match="not found"):
            populated_service.submit_review("doc-1", "nonexistent", ReviewStatus.APPROVED)


class TestDocumentLifecycleApproval:
    def test_approve_document(self, populated_service: DocumentLifecycleService) -> None:
        workflow = DocumentApprovalWorkflow(id="wf-1", name="Standard Approval")
        populated_service.create_workflow(workflow)
        result = populated_service.approve_document(
            "doc-1", "wf-1", approver="admin", comment="approved"
        )
        assert result.document_id == "doc-1"

    def test_approve_missing_workflow_raises(
        self, populated_service: DocumentLifecycleService
    ) -> None:
        with pytest.raises(DocumentApprovalError, match="not found"):
            populated_service.approve_document("doc-1", "nonexistent", approver="admin")

    def test_reject_document(self, populated_service: DocumentLifecycleService) -> None:
        workflow = DocumentApprovalWorkflow(id="wf-1", name="Standard Approval")
        populated_service.create_workflow(workflow)
        result = populated_service.reject_document(
            "doc-1", "wf-1", reviewer="admin", reason="needs work"
        )
        assert result.document_id == "doc-1"


class TestDocumentLifecyclePolicies:
    def test_create_policy(self, service: DocumentLifecycleService) -> None:
        policy = DocumentLifecyclePolicy(id="pol-1", name="Retention Policy")
        result = service.create_policy(policy)
        assert result.id == "pol-1"

    def test_apply_policy(self, service: DocumentLifecycleService) -> None:
        policy = DocumentLifecyclePolicy(id="pol-1", name="Compliance")
        service.create_policy(policy)
        service.create_document("doc-1", "Test")
        service.apply_policy("doc-1", "pol-1")

    def test_apply_missing_policy_raises(self, service: DocumentLifecycleService) -> None:
        service.create_document("doc-1", "Test")
        with pytest.raises(DocumentRetentionError, match="not found"):
            service.apply_policy("doc-1", "nonexistent")


class TestDocumentLifecycleRetention:
    def test_create_retention_policy(self, service: DocumentLifecycleService) -> None:
        policy = DocumentRetentionPolicy(id="ret-1", name="2 Year Retention", retention_days=730)
        result = service.create_retention_policy(policy)
        assert result.id == "ret-1"

    def test_enforce_retention_archive(self, service: DocumentLifecycleService) -> None:
        policy = DocumentRetentionPolicy(
            id="ret-1",
            name="Archive after 2y",
            action_on_expiry="archive",
        )
        service.create_retention_policy(policy)
        service.create_document("doc-1", "Test")
        service.enforce_retention("doc-1", "ret-1")
        doc = service.get_document("doc-1")
        assert doc.status == DocumentLifecycleStatus.ARCHIVED

    def test_enforce_retention_missing_policy_raises(
        self, service: DocumentLifecycleService
    ) -> None:
        service.create_document("doc-1", "Test")
        with pytest.raises(DocumentRetentionError, match="not found"):
            service.enforce_retention("doc-1", "nonexistent")


class TestDocumentLifecycleExpiry:
    def test_set_expiry(self, service: DocumentLifecycleService) -> None:
        service.create_document("doc-1", "Test")
        future = datetime.now() + timedelta(days=30)
        config = DocumentExpiryConfig(id="exp-1", lifecycle_id="doc-1", expires_at=future)
        result = service.set_expiry("doc-1", config)
        assert result.expires_at == future

    def test_check_expiry_warnings(self, service: DocumentLifecycleService) -> None:
        service.create_document("doc-1", "Test")
        near_future = datetime.now() + timedelta(days=5)
        config = DocumentExpiryConfig(
            id="exp-1",
            lifecycle_id="doc-1",
            expires_at=near_future,
            warning_days_before=10,
        )
        service.set_expiry("doc-1", config)
        warnings = service.check_expiry_warnings()
        assert len(warnings) == 1


class TestDocumentLifecycleReport:
    def test_get_report(self, populated_service: DocumentLifecycleService) -> None:
        report = populated_service.get_report()
        assert report.total_documents == 2
        assert report.active_count == 2

    def test_report_after_archive(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.archive_document("doc-1")
        report = populated_service.get_report()
        assert report.active_count == 1
        assert report.archived_count == 1


class TestDocumentLifecycleAudit:
    def test_actions_recorded(self, populated_service: DocumentLifecycleService) -> None:
        actions = populated_service.get_actions("doc-1")
        assert len(actions) >= 1
        assert actions[0].action_type == DocumentLifecycleActionType.CREATE

    def test_audit_trail(self, populated_service: DocumentLifecycleService) -> None:
        populated_service.archive_document("doc-1", actor="admin", reason="done")
        entries = populated_service.get_audit_trail("doc-1")
        actions = [e.action for e in entries]
        assert "create" in actions
        assert "archive" in actions
