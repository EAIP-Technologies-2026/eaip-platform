"""Domain events for the content registry."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ContentCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.created"
    item_id: str = ""
    name: str = ""
    content_type: str = ""
    author: str = ""


class ContentUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.updated"
    item_id: str = ""
    name: str = ""
    version: str = ""
    author: str = ""


class ContentPublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.published"
    item_id: str = ""
    name: str = ""
    version: str = ""
    author: str = ""


class ContentArchived(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.archived"
    item_id: str = ""
    name: str = ""
    author: str = ""


class ContentDeprecated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.deprecated"
    item_id: str = ""
    name: str = ""
    author: str = ""


class VersionCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.version.created"
    item_id: str = ""
    version: str = ""
    change_log: str = ""
    author: str = ""


class WorkflowStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.workflow.started"
    workflow_id: str = ""
    workflow_name: str = ""
    step_count: int = 0


class WorkflowStepCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.workflow.step_completed"
    workflow_id: str = ""
    step_id: str = ""
    step_name: str = ""
    step_type: str = ""


class WorkflowCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.content.workflow.completed"
    workflow_id: str = ""
    workflow_name: str = ""
    status: str = ""


ContentEvent = (
    ContentCreated
    | ContentUpdated
    | ContentPublished
    | ContentArchived
    | ContentDeprecated
    | VersionCreated
    | WorkflowStarted
    | WorkflowStepCompleted
    | WorkflowCompleted
)


__all__ = [
    "ContentArchived",
    "ContentCreated",
    "ContentDeprecated",
    "ContentEvent",
    "ContentPublished",
    "ContentUpdated",
    "VersionCreated",
    "WorkflowCompleted",
    "WorkflowStarted",
    "WorkflowStepCompleted",
]
