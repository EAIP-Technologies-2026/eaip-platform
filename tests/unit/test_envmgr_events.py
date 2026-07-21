"""Tests for envmgr domain events."""

from __future__ import annotations

import pytest

from eaip.envmgr.events import (
    VariableCreated,
    VariableDeleted,
    VariableGroupCreated,
    VariableUpdated,
)
from eaip.events.event import DomainEvent


class TestVariableCreated:
    def test_defaults(self) -> None:
        e = VariableCreated(variable_id="v1", name="DB_HOST", environment="prod")
        assert e.event_type == "eaip.envmgr.variable.created"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = VariableCreated(
            variable_id="v1", name="DB_HOST", environment="prod", scope="global", is_secret=True
        )
        assert e.is_secret is True
        assert e.scope == "global"


class TestVariableUpdated:
    def test_defaults(self) -> None:
        e = VariableUpdated(variable_id="v1", name="DB_HOST", environment="prod")
        assert e.event_type == "eaip.envmgr.variable.updated"
        assert e.version == 1

    def test_with_values(self) -> None:
        e = VariableUpdated(variable_id="v1", name="DB_HOST", environment="prod", version=3)
        assert e.version == 3


class TestVariableDeleted:
    def test_defaults(self) -> None:
        e = VariableDeleted(variable_id="v1", name="DB_HOST", environment="prod")
        assert e.event_type == "eaip.envmgr.variable.deleted"


class TestVariableGroupCreated:
    def test_defaults(self) -> None:
        e = VariableGroupCreated(group_id="g1", name="app-config", environment="prod")
        assert e.event_type == "eaip.envmgr.variable_group.created"
        assert e.variable_count == 0

    def test_with_values(self) -> None:
        e = VariableGroupCreated(
            group_id="g1", name="app-config", environment="prod", variable_count=3
        )
        assert e.variable_count == 3

    def test_frozen(self) -> None:
        e = VariableGroupCreated(group_id="g1", name="app-config", environment="prod")
        with pytest.raises((ValueError, TypeError)):
            e.group_id = "g2"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [VariableCreated, VariableUpdated, VariableDeleted, VariableGroupCreated]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
