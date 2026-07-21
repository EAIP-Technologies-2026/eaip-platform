"""Tests for Content domain events."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.content.events import (
    ContentArchived,
    ContentCreated,
    ContentDeprecated,
    ContentEvent,
    ContentPublished,
    ContentUpdated,
    VersionCreated,
    WorkflowCompleted,
    WorkflowStarted,
    WorkflowStepCompleted,
)
from eaip.events.event import DomainEvent


class TestContentCreated:
    def test_defaults(self) -> None:
        event = ContentCreated()
        assert event.event_type == "eaip.content.created"
        assert event.item_id == ""
        assert event.name == ""
        assert event.content_type == ""
        assert event.author == ""
        assert isinstance(event.occurred_at, datetime)

    def test_with_fields(self) -> None:
        event = ContentCreated(
            item_id="doc_1",
            name="Doc 1",
            content_type="text/plain",
            author="alice",
        )
        assert event.item_id == "doc_1"
        assert event.name == "Doc 1"
        assert event.content_type == "text/plain"
        assert event.author == "alice"

    def test_is_domain_event(self) -> None:
        assert issubclass(ContentCreated, DomainEvent)

    def test_frozen(self) -> None:
        event = ContentCreated()
        with pytest.raises(ValueError):
            event.item_id = "changed"  # type: ignore[misc]


class TestContentUpdated:
    def test_defaults(self) -> None:
        event = ContentUpdated()
        assert event.event_type == "eaip.content.updated"

    def test_with_fields(self) -> None:
        event = ContentUpdated(
            item_id="doc_1",
            name="Doc 1",
            version="0.2.0",
            author="bob",
        )
        assert event.version == "0.2.0"
        assert event.author == "bob"


class TestContentPublished:
    def test_defaults(self) -> None:
        event = ContentPublished()
        assert event.event_type == "eaip.content.published"

    def test_with_fields(self) -> None:
        event = ContentPublished(
            item_id="doc_1",
            name="Doc 1",
            version="1.0.0",
            author="alice",
        )
        assert event.version == "1.0.0"


class TestContentArchived:
    def test_defaults(self) -> None:
        event = ContentArchived()
        assert event.event_type == "eaip.content.archived"

    def test_with_fields(self) -> None:
        event = ContentArchived(item_id="doc_1", name="Doc 1", author="admin")
        assert event.author == "admin"


class TestContentDeprecated:
    def test_defaults(self) -> None:
        event = ContentDeprecated()
        assert event.event_type == "eaip.content.deprecated"

    def test_with_fields(self) -> None:
        event = ContentDeprecated(item_id="doc_1", name="Doc 1", author="admin")
        assert event.item_id == "doc_1"


class TestVersionCreated:
    def test_defaults(self) -> None:
        event = VersionCreated()
        assert event.event_type == "eaip.content.version.created"

    def test_with_fields(self) -> None:
        event = VersionCreated(
            item_id="doc_1",
            version="0.2.0",
            change_log="added section",
            author="alice",
        )
        assert event.change_log == "added section"


class TestWorkflowStarted:
    def test_defaults(self) -> None:
        event = WorkflowStarted()
        assert event.event_type == "eaip.content.workflow.started"

    def test_with_fields(self) -> None:
        event = WorkflowStarted(
            workflow_id="wf_1",
            workflow_name="Publish",
            step_count=3,
        )
        assert event.step_count == 3


class TestWorkflowStepCompleted:
    def test_defaults(self) -> None:
        event = WorkflowStepCompleted()
        assert event.event_type == "eaip.content.workflow.step_completed"

    def test_with_fields(self) -> None:
        event = WorkflowStepCompleted(
            workflow_id="wf_1",
            step_id="s1",
            step_name="Review",
            step_type="review",
        )
        assert event.step_type == "review"


class TestWorkflowCompleted:
    def test_defaults(self) -> None:
        event = WorkflowCompleted()
        assert event.event_type == "eaip.content.workflow.completed"

    def test_with_fields(self) -> None:
        event = WorkflowCompleted(
            workflow_id="wf_1",
            workflow_name="Publish",
            status="completed",
        )
        assert event.status == "completed"


class TestContentEvent:
    def test_union_type(self) -> None:
        events: list[ContentEvent] = [
            ContentCreated(),
            ContentUpdated(),
            ContentPublished(),
            ContentArchived(),
            ContentDeprecated(),
            VersionCreated(),
            WorkflowStarted(),
            WorkflowStepCompleted(),
            WorkflowCompleted(),
        ]
        assert len(events) == 9
