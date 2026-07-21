"""Tests for dbmigrate domain events."""

from __future__ import annotations

import pytest

from eaip.dbmigrate.events import MigrationExecuted, MigrationRolledBack, ScriptCreated
from eaip.events.event import DomainEvent


class TestScriptCreated:
    def test_defaults(self) -> None:
        e = ScriptCreated(
            script_id="s1",
            name="add_users",
            version="1.0",
            database_type="postgres",
            author="alice",
        )
        assert e.event_type == "eaip.dbmigrate.script.created"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = ScriptCreated(
            script_id="s1",
            name="add_users",
            version="1.0",
            database_type="postgres",
            author="alice",
        )
        assert e.script_id == "s1"
        assert e.name == "add_users"
        assert e.version == "1.0"

    def test_frozen(self) -> None:
        e = ScriptCreated(
            script_id="s1",
            name="add_users",
            version="1.0",
            database_type="postgres",
            author="alice",
        )
        with pytest.raises((ValueError, TypeError)):
            e.script_id = "s2"


class TestMigrationExecuted:
    def test_defaults(self) -> None:
        e = MigrationExecuted(execution_id="e1", script_id="s1", environment="prod", success=True)
        assert e.event_type == "eaip.dbmigrate.migration.executed"
        assert e.output == ""

    def test_with_values(self) -> None:
        e = MigrationExecuted(
            execution_id="e1", script_id="s1", environment="prod", success=True, output="ok"
        )
        assert e.success is True
        assert e.output == "ok"


class TestMigrationRolledBack:
    def test_defaults(self) -> None:
        e = MigrationRolledBack(script_id="s1", environment="prod")
        assert e.event_type == "eaip.dbmigrate.migration.rolled_back"
        assert e.reason == ""

    def test_with_values(self) -> None:
        e = MigrationRolledBack(script_id="s1", environment="prod", reason="data issue")
        assert e.reason == "data issue"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [ScriptCreated, MigrationExecuted, MigrationRolledBack]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
