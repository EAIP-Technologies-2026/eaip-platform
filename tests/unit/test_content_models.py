"""Tests for Content domain models."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.content.models import (
    ContentConfig,
    ContentItem,
    ContentStatus,
    ContentType,
    ContentVersion,
    PublishingWorkflow,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowStepType,
)


class TestContentType:
    def test_values(self) -> None:
        assert ContentType.DOCUMENT == "document"
        assert ContentType.IMAGE == "image"
        assert ContentType.CONFIG == "config"
        assert ContentType.TEMPLATE == "template"
        assert ContentType.SCRIPT == "script"

    def test_valid_members(self) -> None:
        assert len(ContentType) == 5


class TestContentStatus:
    def test_values(self) -> None:
        assert ContentStatus.DRAFT == "draft"
        assert ContentStatus.PUBLISHED == "published"
        assert ContentStatus.ARCHIVED == "archived"
        assert ContentStatus.DEPRECATED == "deprecated"

    def test_valid_members(self) -> None:
        assert len(ContentStatus) == 4


class TestContentItem:
    def test_required_fields(self) -> None:
        item = ContentItem(
            id="item_1",
            name="Test Document",
            type=ContentType.DOCUMENT,
            content_type="application/pdf",
            body="content body",
        )
        assert item.id == "item_1"
        assert item.name == "Test Document"
        assert item.type is ContentType.DOCUMENT
        assert item.content_type == "application/pdf"
        assert item.body == "content body"
        assert item.version == "0.1.0"
        assert item.status is ContentStatus.DRAFT
        assert item.tags == ()
        assert item.metadata == {}
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
        assert item.published_at is None
        assert item.author == ""
        assert item.checksum == ""
        assert item.content_hash == ""

    def test_frozen(self) -> None:
        item = ContentItem(
            id="i1",
            name="N",
            type=ContentType.DOCUMENT,
            content_type="text",
            body="b",
        )
        with pytest.raises(ValueError):
            item.name = "changed"  # type: ignore[misc]

    def test_published_at(self) -> None:
        now = datetime.now()
        item = ContentItem(
            id="i1",
            name="N",
            type=ContentType.DOCUMENT,
            content_type="text",
            body="b",
            status=ContentStatus.PUBLISHED,
            published_at=now,
        )
        assert item.status is ContentStatus.PUBLISHED
        assert item.published_at == now

    def test_with_tags_and_metadata(self) -> None:
        item = ContentItem(
            id="i1",
            name="N",
            type=ContentType.CONFIG,
            content_type="application/json",
            body="{}",
            tags=("config", "env"),
            metadata={"env": "prod"},
        )
        assert item.tags == ("config", "env")
        assert item.metadata == {"env": "prod"}


class TestContentVersion:
    def test_required_fields(self) -> None:
        v = ContentVersion(
            id="v1",
            item_id="item_1",
            version="0.2.0",
            body="updated body",
        )
        assert v.id == "v1"
        assert v.item_id == "item_1"
        assert v.version == "0.2.0"
        assert v.body == "updated body"
        assert v.checksum == ""
        assert v.change_log == ""
        assert v.author == ""
        assert isinstance(v.created_at, datetime)

    def test_frozen(self) -> None:
        v = ContentVersion(id="v1", item_id="i1", version="1.0", body="b")
        with pytest.raises(ValueError):
            v.version = "2.0"  # type: ignore[misc]

    def test_with_all_fields(self) -> None:
        v = ContentVersion(
            id="v1",
            item_id="i1",
            version="1.0",
            body="b",
            checksum="abc123",
            change_log="initial",
            author="alice",
            metadata={"reason": "update"},
        )
        assert v.checksum == "abc123"
        assert v.change_log == "initial"
        assert v.author == "alice"
        assert v.metadata == {"reason": "update"}


class TestWorkflowStep:
    def test_required_fields(self) -> None:
        s = WorkflowStep(id="s1", name="Review", type=WorkflowStepType.REVIEW)
        assert s.id == "s1"
        assert s.name == "Review"
        assert s.type is WorkflowStepType.REVIEW
        assert s.assignees == ()
        assert s.status is WorkflowStepStatus.PENDING
        assert s.timeout_hours == 0.0
        assert s.metadata == {}

    def test_with_assignees(self) -> None:
        s = WorkflowStep(
            id="s1",
            name="Approve",
            type=WorkflowStepType.APPROVAL,
            assignees=("alice", "bob"),
            timeout_hours=24.0,
        )
        assert s.assignees == ("alice", "bob")
        assert s.timeout_hours == 24.0

    def test_frozen(self) -> None:
        s = WorkflowStep(id="s1", name="N", type=WorkflowStepType.REVIEW)
        with pytest.raises(ValueError):
            s.name = "changed"  # type: ignore[misc]


class TestPublishingWorkflow:
    def test_required_fields(self) -> None:
        w = PublishingWorkflow(id="wf_1", name="Deploy Workflow")
        assert w.id == "wf_1"
        assert w.name == "Deploy Workflow"
        assert w.steps == ()
        assert w.status is WorkflowStatus.PENDING
        assert isinstance(w.created_at, datetime)

    def test_with_steps(self) -> None:
        steps = (
            WorkflowStep(id="s1", name="Review", type=WorkflowStepType.REVIEW),
            WorkflowStep(id="s2", name="Approve", type=WorkflowStepType.APPROVAL),
        )
        w = PublishingWorkflow(id="wf_1", name="Publishing", steps=steps)
        assert len(w.steps) == 2
        assert w.steps[0].name == "Review"

    def test_frozen(self) -> None:
        w = PublishingWorkflow(id="wf_1", name="W")
        with pytest.raises(ValueError):
            w.name = "changed"  # type: ignore[misc]


class TestContentConfig:
    def test_defaults(self) -> None:
        c = ContentConfig()
        assert c.max_versions_per_item == 10
        assert c.enable_versioning is True
        assert c.enable_workflow is True
        assert c.default_status is ContentStatus.DRAFT
        assert c.storage_backend == "memory"
        assert c.cache_ttl_seconds == 300
        assert len(c.allowed_types) == 5

    def test_custom(self) -> None:
        c = ContentConfig(
            max_versions_per_item=5,
            enable_versioning=False,
            default_status=ContentStatus.PUBLISHED,
            storage_backend="s3",
        )
        assert c.max_versions_per_item == 5
        assert c.enable_versioning is False
        assert c.default_status is ContentStatus.PUBLISHED
        assert c.storage_backend == "s3"

    def test_frozen(self) -> None:
        c = ContentConfig()
        with pytest.raises(ValueError):
            c.max_versions_per_item = 20  # type: ignore[misc]


class TestWorkflowStepType:
    def test_values(self) -> None:
        assert WorkflowStepType.REVIEW == "review"
        assert WorkflowStepType.APPROVAL == "approval"
        assert WorkflowStepType.PUBLISH == "publish"
        assert WorkflowStepType.NOTIFY == "notify"


class TestWorkflowStepStatus:
    def test_values(self) -> None:
        assert WorkflowStepStatus.PENDING == "pending"
        assert WorkflowStepStatus.RUNNING == "running"
        assert WorkflowStepStatus.COMPLETED == "completed"
        assert WorkflowStepStatus.FAILED == "failed"
        assert WorkflowStepStatus.TIMED_OUT == "timed_out"


class TestWorkflowStatus:
    def test_values(self) -> None:
        assert WorkflowStatus.PENDING == "pending"
        assert WorkflowStatus.RUNNING == "running"
        assert WorkflowStatus.COMPLETED == "completed"
        assert WorkflowStatus.FAILED == "failed"
        assert WorkflowStatus.CANCELLED == "cancelled"
