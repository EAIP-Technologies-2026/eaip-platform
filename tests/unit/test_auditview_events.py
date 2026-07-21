"""Tests for auditview domain events."""

from __future__ import annotations

from eaip.auditview.events import AuditExported, EntryIngested
from eaip.events.event import DomainEvent


class TestEntryIngested:
    def test_event_type(self) -> None:
        event = EntryIngested(entry_id="e1", actor="user1", action="create", resource="res:1")
        assert event.event_type == "eaip.auditview.entry.ingested"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = EntryIngested(entry_id="e1", actor="user1", action="create", resource="res:1")
        assert event.entry_id == "e1"
        assert event.actor == "user1"
        assert event.action == "create"
        assert event.resource == "res:1"


class TestAuditExported:
    def test_event_type(self) -> None:
        event = AuditExported(
            filter_actor=None,
            filter_action=None,
            filter_resource=None,
            entry_count=10,
        )
        assert event.event_type == "eaip.auditview.audit.exported"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = AuditExported(
            filter_actor="user1",
            filter_action="create",
            filter_resource="res:1",
            entry_count=5,
        )
        assert event.filter_actor == "user1"
        assert event.filter_action == "create"
        assert event.entry_count == 5


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(EntryIngested, DomainEvent)
        assert issubclass(AuditExported, DomainEvent)
