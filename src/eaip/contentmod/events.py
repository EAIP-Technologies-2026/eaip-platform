"""Domain events for the content moderation service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ContentSubmitted(DomainEvent):
    event_type: ClassVar[str] = "eaip.contentmod.content.submitted"
    content_id: str
    source: str
    content_type: str


class ContentApproved(DomainEvent):
    event_type: ClassVar[str] = "eaip.contentmod.content.approved"
    content_id: str
    moderated_by: str


class ContentRejected(DomainEvent):
    event_type: ClassVar[str] = "eaip.contentmod.content.rejected"
    content_id: str
    reason: str
    moderated_by: str


class ContentFlagged(DomainEvent):
    event_type: ClassVar[str] = "eaip.contentmod.content.flagged"
    content_id: str
    rule_id: str
    reason: str


__all__ = [
    "ContentApproved",
    "ContentFlagged",
    "ContentRejected",
    "ContentSubmitted",
]
