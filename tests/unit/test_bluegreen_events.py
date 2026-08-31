"""Tests for bluegreen domain events."""

from __future__ import annotations

from eaip.bluegreen.events import (
    HealthCheckFailed,
    SwitchCompleted,
    SwitchRolledBack,
    SwitchStarted,
)
from eaip.events.event import DomainEvent


class TestSwitchStarted:
    def test_event_type(self) -> None:
        event = SwitchStarted(
            switch_id="sw1", from_env="blue", to_env="green", strategy="health_check"
        )
        assert event.event_type == "eaip.bluegreen.switch.started"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SwitchStarted(
            switch_id="sw1", from_env="blue", to_env="green", strategy="immediate"
        )
        assert event.switch_id == "sw1"
        assert event.from_env == "blue"
        assert event.to_env == "green"
        assert event.strategy == "immediate"


class TestSwitchCompleted:
    def test_event_type(self) -> None:
        event = SwitchCompleted(
            switch_id="sw1", from_env="blue", to_env="green", new_active="green"
        )
        assert event.event_type == "eaip.bluegreen.switch.completed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SwitchCompleted(
            switch_id="sw1", from_env="blue", to_env="green", new_active="green"
        )
        assert event.switch_id == "sw1"
        assert event.new_active == "green"


class TestSwitchRolledBack:
    def test_event_type(self) -> None:
        event = SwitchRolledBack(switch_id="sw1", from_env="blue", to_env="green", reason="failure")
        assert event.event_type == "eaip.bluegreen.switch.rolled_back"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = SwitchRolledBack(
            switch_id="sw1", from_env="blue", to_env="green", reason="Health check failed"
        )
        assert event.switch_id == "sw1"
        assert event.reason == "Health check failed"


class TestHealthCheckFailed:
    def test_event_type(self) -> None:
        event = HealthCheckFailed(switch_id="sw1", environment="green", message="Timeout")
        assert event.event_type == "eaip.bluegreen.health_check.failed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = HealthCheckFailed(switch_id="sw1", environment="green", message="Unhealthy")
        assert event.switch_id == "sw1"
        assert event.environment == "green"
        assert event.message == "Unhealthy"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(SwitchStarted, DomainEvent)
        assert issubclass(SwitchCompleted, DomainEvent)
        assert issubclass(SwitchRolledBack, DomainEvent)
        assert issubclass(HealthCheckFailed, DomainEvent)
