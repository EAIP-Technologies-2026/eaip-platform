"""Tests for bcalendar domain events."""

from __future__ import annotations

from eaip.bcalendar.events import (
    AvailabilityChecked,
    EventCancelled,
    EventCreated,
    EventUpdated,
)
from eaip.events.event import DomainEvent


class TestEventCreated:
    def test_event_type(self) -> None:
        event = EventCreated(event_id="e1", title="Meeting")
        assert event.event_type == "eaip.bcalendar.event.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = EventCreated(event_id="e1", title="Meeting")
        assert event.event_id == "e1"
        assert event.title == "Meeting"


class TestEventUpdated:
    def test_event_type(self) -> None:
        event = EventUpdated(event_id="e1", changes={"title": "New"})
        assert event.event_type == "eaip.bcalendar.event.updated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = EventUpdated(event_id="e1", changes={"title": "New"})
        assert event.event_id == "e1"
        assert event.changes == {"title": "New"}


class TestEventCancelled:
    def test_event_type(self) -> None:
        event = EventCancelled(event_id="e1", reason="Cancelled")
        assert event.event_type == "eaip.bcalendar.event.cancelled"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = EventCancelled(event_id="e1", reason="No longer needed")
        assert event.event_id == "e1"
        assert event.reason == "No longer needed"


class TestAvailabilityChecked:
    def test_event_type(self) -> None:
        event = AvailabilityChecked(date="2025-06-01", available=True)
        assert event.event_type == "eaip.bcalendar.availability.checked"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AvailabilityChecked(date="2025-06-01", available=True)
        assert event.date == "2025-06-01"
        assert event.available is True


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(EventCreated, DomainEvent)
        assert issubclass(EventUpdated, DomainEvent)
        assert issubclass(EventCancelled, DomainEvent)
        assert issubclass(AvailabilityChecked, DomainEvent)
