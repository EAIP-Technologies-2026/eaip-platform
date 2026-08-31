"""Domain events for batch job scheduling."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class BatchJobCreated(DomainEvent):
    """Emitted when a new batch job is created."""

    event_type: ClassVar[str] = "eaip.batchjob.created"

    job_id: str
    name: str
    job_type: str
    parameters: dict[str, Any]


class BatchJobStarted(DomainEvent):
    """Emitted when a batch job execution begins."""

    event_type: ClassVar[str] = "eaip.batchjob.started"

    job_id: str
    execution_id: str


class BatchJobCompleted(DomainEvent):
    """Emitted when a batch job completes successfully."""

    event_type: ClassVar[str] = "eaip.batchjob.completed"

    job_id: str
    execution_id: str
    result: dict[str, Any]


class BatchJobFailed(DomainEvent):
    """Emitted when a batch job execution fails."""

    event_type: ClassVar[str] = "eaip.batchjob.failed"

    job_id: str
    execution_id: str
    error: str
    retry_count: int


__all__ = [
    "BatchJobCompleted",
    "BatchJobCreated",
    "BatchJobFailed",
    "BatchJobStarted",
]
