"""Domain events for emergency access management."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class AccessRequested(DomainEvent):
    """Emitted when an emergency access request is created."""

    event_type: ClassVar[str] = "eaip.emergency.access.requested"

    request_id: str
    requester_id: str
    resource: str
    duration_minutes: int


class AccessApproved(DomainEvent):
    """Emitted when an emergency access request is approved."""

    event_type: ClassVar[str] = "eaip.emergency.access.approved"

    request_id: str
    approver_id: str


class AccessRejected(DomainEvent):
    """Emitted when an emergency access request is rejected."""

    event_type: ClassVar[str] = "eaip.emergency.access.rejected"

    request_id: str
    approver_id: str
    reason: str


class AccessExpired(DomainEvent):
    """Emitted when an emergency access request expires."""

    event_type: ClassVar[str] = "eaip.emergency.access.expired"

    request_id: str


__all__ = [
    "AccessApproved",
    "AccessExpired",
    "AccessRejected",
    "AccessRequested",
]
