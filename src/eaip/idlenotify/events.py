"""Domain events for idle resource notification."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.idlenotify.models import ResourceStatus, Severity


class ResourceMarkedIdle(DomainEvent):
    """Emitted when a resource transitions to an idle status."""

    event_type: ClassVar[str] = "eaip.idlenotify.resource.marked_idle"

    resource_id: str
    resource_name: str
    previous_status: ResourceStatus
    new_status: ResourceStatus


class IdleNotificationSent(DomainEvent):
    """Emitted when an idle notification is sent."""

    event_type: ClassVar[str] = "eaip.idlenotify.notification.sent"

    notification_id: str
    resource_id: str
    severity: Severity
    idle_duration: float = Field(default=0.0)
    sent_at: datetime = Field(default_factory=datetime.now)


class ResourceArchived(DomainEvent):
    """Emitted when a resource is archived due to prolonged idleness."""

    event_type: ClassVar[str] = "eaip.idlenotify.resource.archived"

    resource_id: str
    resource_name: str
    idle_duration_hours: float = Field(default=0.0)


__all__ = [
    "IdleNotificationSent",
    "ResourceArchived",
    "ResourceMarkedIdle",
]
