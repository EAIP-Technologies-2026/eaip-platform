"""Domain events for incident communication."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.inccomm.models import Channel, CommStatus, PageStatus


class NotificationSent(DomainEvent):
    """Emitted when an incident notification is sent."""

    event_type: ClassVar[str] = "eaip.inccomm.notification.sent"

    comm_id: str
    incident_id: str
    channel: Channel
    status: CommStatus


class StatusPageUpdated(DomainEvent):
    """Emitted when a status page is updated."""

    event_type: ClassVar[str] = "eaip.inccomm.status_page.updated"

    page_id: str
    incident_id: str
    new_status: PageStatus


class IncidentEscalated(DomainEvent):
    """Emitted when an incident is escalated."""

    event_type: ClassVar[str] = "eaip.inccomm.incident.escalated"

    incident_id: str
    previous_status: PageStatus
    new_status: PageStatus
    escalation_level: int


__all__ = [
    "IncidentEscalated",
    "NotificationSent",
    "StatusPageUpdated",
]
