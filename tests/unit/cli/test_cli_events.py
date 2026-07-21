"""Tests for CLI domain events."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.cli.events import (
    CliEvent,
    CliSessionEnded,
    CliSessionStarted,
    CommandExecuted,
    ShellCommandRegistered,
)
from eaip.events.event import DomainEvent


class TestCliSessionStarted:
    def test_defaults(self) -> None:
        event = CliSessionStarted()
        assert event.event_type == "eaip.cli.session.started"
        assert event.session_id == ""
        assert isinstance(event.occurred_at, datetime)

    def test_with_fields(self) -> None:
        event = CliSessionStarted(session_id="sess_1")
        assert event.session_id == "sess_1"

    def test_is_domain_event(self) -> None:
        assert issubclass(CliSessionStarted, DomainEvent)

    def test_frozen(self) -> None:
        event = CliSessionStarted()
        with pytest.raises(ValueError):
            event.session_id = "changed"  # type: ignore[misc]


class TestCliSessionEnded:
    def test_defaults(self) -> None:
        event = CliSessionEnded()
        assert event.event_type == "eaip.cli.session.ended"
        assert event.session_id == ""
        assert event.command_count == 0
        assert event.duration_ms == 0

    def test_with_fields(self) -> None:
        event = CliSessionEnded(
            session_id="sess_1",
            command_count=5,
            duration_ms=12000,
        )
        assert event.session_id == "sess_1"
        assert event.command_count == 5
        assert event.duration_ms == 12000


class TestCommandExecuted:
    def test_defaults(self) -> None:
        event = CommandExecuted()
        assert event.event_type == "eaip.cli.command.executed"
        assert event.command_name == ""
        assert event.success is True
        assert event.duration_ms == 0
        assert event.error == ""

    def test_with_fields(self) -> None:
        event = CommandExecuted(
            command_name="deploy",
            success=False,
            duration_ms=500,
            error="timeout",
        )
        assert event.command_name == "deploy"
        assert event.success is False
        assert event.duration_ms == 500
        assert event.error == "timeout"


class TestShellCommandRegistered:
    def test_defaults(self) -> None:
        event = ShellCommandRegistered()
        assert event.event_type == "eaip.cli.shell.command_registered"
        assert event.command_name == ""
        assert event.description == ""

    def test_with_fields(self) -> None:
        event = ShellCommandRegistered(
            command_name="deploy",
            description="Deploy to environment",
        )
        assert event.command_name == "deploy"
        assert event.description == "Deploy to environment"


class TestCliEvent:
    def test_union_type(self) -> None:
        events: list[CliEvent] = [
            CliSessionStarted(),
            CliSessionEnded(),
            CommandExecuted(),
            ShellCommandRegistered(),
        ]
        assert len(events) == 4
