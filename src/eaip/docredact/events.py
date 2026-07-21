"""Domain events for document redaction."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class JobCreated(DomainEvent):
    """Emitted when a redaction job is created."""

    event_type: ClassVar[str] = "eaip.docredact.job.created"

    job_id: str
    document_ref: str
    rules_count: int


class RedactionCompleted(DomainEvent):
    """Emitted when a redaction job completes successfully."""

    event_type: ClassVar[str] = "eaip.docredact.redaction.completed"

    job_id: str
    document_ref: str
    rules_applied: list[str]


class RedactionFailed(DomainEvent):
    """Emitted when a redaction job fails."""

    event_type: ClassVar[str] = "eaip.docredact.redaction.failed"

    job_id: str
    document_ref: str
    reason: str


__all__ = [
    "JobCreated",
    "RedactionCompleted",
    "RedactionFailed",
]
