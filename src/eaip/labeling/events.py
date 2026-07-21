"""Domain events for data labeling."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class TaskCreated(DomainEvent):
    """Emitted when a labeling task is created."""

    event_type: ClassVar[str] = "eaip.labeling.task.created"

    task_id: str
    name: str
    label_count: int


class TaskCompleted(DomainEvent):
    """Emitted when a labeling task is completed."""

    event_type: ClassVar[str] = "eaip.labeling.task.completed"

    task_id: str
    total_labels: int


class LabelSubmitted(DomainEvent):
    """Emitted when a label is submitted."""

    event_type: ClassVar[str] = "eaip.labeling.label.submitted"

    label_id: str
    task_id: str
    labeler_id: str
    value: str


class LabelReviewed(DomainEvent):
    """Emitted when a label is reviewed."""

    event_type: ClassVar[str] = "eaip.labeling.label.reviewed"

    label_id: str
    task_id: str
    approved: bool


__all__ = [
    "LabelReviewed",
    "LabelSubmitted",
    "TaskCompleted",
    "TaskCreated",
]
