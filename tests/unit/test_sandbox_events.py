"""Tests for sandbox domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.sandbox.events import (
    EnvironmentCreated,
    EnvironmentDeleted,
    SandboxCreated,
    SandboxExpired,
    SandboxStopped,
)


class TestEnvironmentCreated:
    def test_event_type(self) -> None:
        event = EnvironmentCreated(environment_id="e1", name="Dev", environment_type="dev")
        assert event.event_type == "eaip.sandbox.environment.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = EnvironmentCreated(environment_id="e1", name="Dev", environment_type="dev")
        assert event.environment_id == "e1"
        assert event.name == "Dev"
        assert event.environment_type == "dev"


class TestEnvironmentDeleted:
    def test_event_type(self) -> None:
        event = EnvironmentDeleted(environment_id="e1")
        assert event.event_type == "eaip.sandbox.environment.deleted"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = EnvironmentDeleted(environment_id="e1")
        assert event.environment_id == "e1"


class TestSandboxCreated:
    def test_event_type(self) -> None:
        event = SandboxCreated(
            sandbox_id="sb1",
            name="test",
            environment_id="e1",
            template_id="t1",
            ttl_minutes=60,
            expires_at="2025-01-01T00:00:00Z",
        )
        assert event.event_type == "eaip.sandbox.sandbox.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SandboxCreated(
            sandbox_id="sb1",
            name="test",
            environment_id="e1",
            template_id="t1",
            ttl_minutes=60,
            expires_at="2025-01-01T00:00:00Z",
        )
        assert event.sandbox_id == "sb1"
        assert event.name == "test"
        assert event.ttl_minutes == 60


class TestSandboxStopped:
    def test_event_type(self) -> None:
        event = SandboxStopped(sandbox_id="sb1", environment_id="e1", reason="manual")
        assert event.event_type == "eaip.sandbox.sandbox.stopped"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SandboxStopped(sandbox_id="sb1", environment_id="e1", reason="manual")
        assert event.sandbox_id == "sb1"
        assert event.reason == "manual"


class TestSandboxExpired:
    def test_event_type(self) -> None:
        event = SandboxExpired(
            sandbox_id="sb1", environment_id="e1", expires_at="2025-01-01T00:00:00Z"
        )
        assert event.event_type == "eaip.sandbox.sandbox.expired"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SandboxExpired(
            sandbox_id="sb1", environment_id="e1", expires_at="2025-01-01T00:00:00Z"
        )
        assert event.sandbox_id == "sb1"
        assert event.environment_id == "e1"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(EnvironmentCreated, DomainEvent)
        assert issubclass(EnvironmentDeleted, DomainEvent)
        assert issubclass(SandboxCreated, DomainEvent)
        assert issubclass(SandboxStopped, DomainEvent)
        assert issubclass(SandboxExpired, DomainEvent)
