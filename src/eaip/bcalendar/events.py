"""Domain events for the business calendar service."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class EventCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.bcalendar.event.created"

    event_id: str
    title: str


class EventUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.bcalendar.event.updated"

    event_id: str
    changes: dict[str, Any]


class EventCancelled(DomainEvent):
    event_type: ClassVar[str] = "eaip.bcalendar.event.cancelled"

    event_id: str
    reason: str


class AvailabilityChecked(DomainEvent):
    event_type: ClassVar[str] = "eaip.bcalendar.availability.checked"

    date: str
    available: bool


__all__ = [
    "AvailabilityChecked",
    "EventCancelled",
    "EventCreated",
    "EventUpdated",
]
