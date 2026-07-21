"""Domain events for the knowledge curation service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ContentSubmitted(DomainEvent):
    """Emitted when new content is submitted for curation."""

    event_type: ClassVar[str] = "eaip.curation.content.submitted"

    submission_id: str
    source: str
    content_type: str
    submitted_by: str


class ContentApproved(DomainEvent):
    """Emitted when submitted content is approved."""

    event_type: ClassVar[str] = "eaip.curation.content.approved"

    submission_id: str
    reviewer: str
    score: float | None


class ContentRejected(DomainEvent):
    """Emitted when submitted content is rejected."""

    event_type: ClassVar[str] = "eaip.curation.content.rejected"

    submission_id: str
    reviewer: str
    reason: str


class ContentFlagged(DomainEvent):
    """Emitted when submitted content is flagged for review."""

    event_type: ClassVar[str] = "eaip.curation.content.flagged"

    submission_id: str
    flagged_by: str
    reason: str


__all__ = [
    "ContentApproved",
    "ContentFlagged",
    "ContentRejected",
    "ContentSubmitted",
]
