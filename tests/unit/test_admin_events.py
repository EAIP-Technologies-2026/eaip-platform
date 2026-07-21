"""Tests for :mod:`eaip.admin.events`."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.admin.events import (
    AdminActionExecuted,
    AuditEntryCreated,
    CapabilityToggled,
    ConfigChanged,
    PluginReloaded,
)
from eaip.events.event import DomainEvent


class TestAdminEvents:
    def test_admin_action_executed(self) -> None:
        event = AdminActionExecuted(
            action_id="a-1",
            action_type="restart",
            target="runtime",
            performed_by="admin",
            result="success",
        )
        assert event.event_type == "eaip.admin.action_executed"
        assert isinstance(event, DomainEvent)
        assert event.action_id == "a-1"

    def test_admin_action_executed_with_details(self) -> None:
        event = AdminActionExecuted(
            action_id="a-2",
            action_type="deploy",
            target="plugin:foo",
            performed_by="bot",
            result="failure",
            details={"error": "timeout"},
        )
        assert event.details == {"error": "timeout"}

    def test_audit_entry_created(self) -> None:
        event = AuditEntryCreated(
            entry_id="e-1",
            actor_id="user-1",
            action="delete",
            resource_type="config",
            resource_id="cfg-1",
            outcome="success",
        )
        assert event.event_type == "eaip.admin.audit_entry_created"
        assert event.actor_id == "user-1"

    def test_config_changed(self) -> None:
        event = ConfigChanged(
            key="logging.level",
            old_value="INFO",
            new_value="DEBUG",
            changed_by="admin",
        )
        assert event.event_type == "eaip.admin.config_changed"
        assert event.key == "logging.level"
        assert event.new_value == "DEBUG"

    def test_capability_toggled(self) -> None:
        event = CapabilityToggled(
            name="metrics",
            enabled=True,
            toggled_by="operator",
        )
        assert event.event_type == "eaip.admin.capability_toggled"
        assert event.name == "metrics"
        assert event.enabled is True

    def test_plugin_reloaded(self) -> None:
        event = PluginReloaded(
            plugin_name="my-plugin",
            success=True,
            message="ok",
        )
        assert event.event_type == "eaip.admin.plugin_reloaded"
        assert event.plugin_name == "my-plugin"
        assert event.success is True

    def test_events_are_frozen(self) -> None:
        event = PluginReloaded(plugin_name="p", success=True)
        with pytest.raises(ValueError):
            event.plugin_name = "other"  # type: ignore[misc]

    def test_events_have_occurred_at(self) -> None:
        event = AuditEntryCreated(
            entry_id="e1",
            actor_id="u1",
            action="read",
            resource_type="log",
            resource_id="l1",
            outcome="success",
        )
        assert isinstance(event.occurred_at, datetime)
