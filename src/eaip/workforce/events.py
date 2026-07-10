"""Workforce domain events — published via EventBus during workforce lifecycle."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.events.event import DomainEvent
from eaip.shared.time import utc_now


class WorkerRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.workforce.worker.registered"
    worker_id: str = ""
    worker_name: str = ""
    worker_type: str = ""
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = {}


class WorkerUnregistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.workforce.worker.unregistered"
    worker_id: str = ""
    worker_name: str = ""
    worker_type: str = ""


class WorkerAssigned(DomainEvent):
    event_type: ClassVar[str] = "eaip.workforce.worker.assigned"
    assignment_id: str = ""
    worker_id: str = ""
    task_description: str = ""
    priority: int = 0


class WorkerAssignmentCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.workforce.worker.assignment_completed"
    assignment_id: str = ""
    worker_id: str = ""
    result: str = ""
    duration_ms: float = 0.0


class WorkerAssignmentFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.workforce.worker.assignment_failed"
    assignment_id: str = ""
    worker_id: str = ""
    error: str = ""


class WorkerScheduled(DomainEvent):
    event_type: ClassVar[str] = "eaip.workforce.worker.scheduled"
    worker_id: str = ""
    worker_name: str = ""
    schedule: str = ""
    one_shot: bool = False


WorkforceEvent = (
    WorkerRegistered
    | WorkerUnregistered
    | WorkerAssigned
    | WorkerAssignmentCompleted
    | WorkerAssignmentFailed
    | WorkerScheduled
)


__all__ = [
    "WorkerAssigned",
    "WorkerAssignmentCompleted",
    "WorkerAssignmentFailed",
    "WorkerRegistered",
    "WorkerScheduled",
    "WorkerUnregistered",
    "WorkforceEvent",
]
