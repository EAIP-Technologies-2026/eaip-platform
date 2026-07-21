"""Tests for retention domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.retention.events import (
    PolicyCreated,
    PolicyDeleted,
    PolicyUpdated,
    PurgeExecuted,
)


class TestPolicyCreated:
    def test_event_type(self) -> None:
        event = PolicyCreated(policy_id="p1", name="Clean logs")
        assert event.event_type == "eaip.retention.policy.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PolicyCreated(policy_id="p1", name="Clean logs")
        assert event.policy_id == "p1"
        assert event.name == "Clean logs"


class TestPolicyUpdated:
    def test_event_type(self) -> None:
        event = PolicyUpdated(policy_id="p1", changes={"name": "New"})
        assert event.event_type == "eaip.retention.policy.updated"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PolicyUpdated(policy_id="p1", changes={"name": "New"})
        assert event.policy_id == "p1"
        assert event.changes == {"name": "New"}


class TestPolicyDeleted:
    def test_event_type(self) -> None:
        event = PolicyDeleted(policy_id="p1")
        assert event.event_type == "eaip.retention.policy.deleted"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PolicyDeleted(policy_id="p1")
        assert event.policy_id == "p1"


class TestPurgeExecuted:
    def test_event_type(self) -> None:
        event = PurgeExecuted(job_id="j1", policy_id="p1", status="completed")
        assert event.event_type == "eaip.retention.purge.executed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = PurgeExecuted(job_id="j1", policy_id="p1", status="completed")
        assert event.job_id == "j1"
        assert event.policy_id == "p1"
        assert event.status == "completed"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(PolicyCreated, DomainEvent)
        assert issubclass(PolicyUpdated, DomainEvent)
        assert issubclass(PolicyDeleted, DomainEvent)
        assert issubclass(PurgeExecuted, DomainEvent)
