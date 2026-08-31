"""Tests for configmgt domain events."""

from __future__ import annotations

from eaip.configmgt.events import (
    ConfigCreated,
    ConfigDeleted,
    ConfigHotReloaded,
    ConfigProfileApplied,
    ConfigProfileCreated,
    ConfigSnapshotCreated,
    ConfigUpdated,
    ConfigValidated,
    ConfigValidationFailed,
)
from eaip.configmgt.models import ConfigEntry, ConfigProfile, ConfigSnapshot
from eaip.events.event import DomainEvent


class TestConfigCreated:
    def test_event_type(self) -> None:
        e = ConfigEntry(id="e1", key="db.host", value="localhost")
        event = ConfigCreated(entry=e)
        assert event.event_type == "configmgt.config.created"
        assert isinstance(event, DomainEvent)

    def test_entry_content(self) -> None:
        e = ConfigEntry(id="e1", key="db.host", value="localhost")
        event = ConfigCreated(entry=e)
        assert event.entry.id == "e1"
        assert event.entry.key == "db.host"


class TestConfigUpdated:
    def test_event_type(self) -> None:
        e = ConfigEntry(id="e1", key="k", value="v2")
        event = ConfigUpdated(entry=e, old_value="v1", changed_by="admin")
        assert event.event_type == "configmgt.config.updated"

    def test_fields(self) -> None:
        e = ConfigEntry(id="e1", key="k", value="v2")
        event = ConfigUpdated(entry=e, old_value="v1", changed_by="admin")
        assert event.old_value == "v1"
        assert event.changed_by == "admin"


class TestConfigDeleted:
    def test_event_type(self) -> None:
        event = ConfigDeleted(entry_id="e1", entry_key="db.host")
        assert event.event_type == "configmgt.config.deleted"

    def test_fields(self) -> None:
        event = ConfigDeleted(entry_id="e1", entry_key="db.host")
        assert event.entry_id == "e1"
        assert event.entry_key == "db.host"


class TestConfigProfileCreated:
    def test_event_type(self) -> None:
        p = ConfigProfile(id="p1", name="Production")
        event = ConfigProfileCreated(profile=p)
        assert event.event_type == "configmgt.profile.created"

    def test_profile_content(self) -> None:
        p = ConfigProfile(id="p1", name="Production", environment="prod")
        event = ConfigProfileCreated(profile=p)
        assert event.profile.id == "p1"
        assert event.profile.environment == "prod"


class TestConfigProfileApplied:
    def test_event_type(self) -> None:
        event = ConfigProfileApplied(profile_id="p1", profile_name="Prod", entries_count=3)
        assert event.event_type == "configmgt.profile.applied"

    def test_fields(self) -> None:
        event = ConfigProfileApplied(profile_id="p1", profile_name="Production", entries_count=5)
        assert event.profile_id == "p1"
        assert event.entries_count == 5


class TestConfigSnapshotCreated:
    def test_event_type(self) -> None:
        s = ConfigSnapshot(id="snap1", profile_id="p1")
        event = ConfigSnapshotCreated(snapshot=s)
        assert event.event_type == "configmgt.snapshot.created"

    def test_snapshot_content(self) -> None:
        s = ConfigSnapshot(id="snap1", profile_id="p1", checksum="abc123")
        event = ConfigSnapshotCreated(snapshot=s)
        assert event.snapshot.id == "snap1"
        assert event.snapshot.checksum == "abc123"


class TestConfigValidated:
    def test_event_type(self) -> None:
        event = ConfigValidated(entry_id="e1", valid=True)
        assert event.event_type == "configmgt.config.validated"

    def test_fields(self) -> None:
        event = ConfigValidated(entry_id="e1", valid=False, errors=("bad",), warnings=("warn",))
        assert event.valid is False
        assert event.errors == ("bad",)
        assert event.warnings == ("warn",)


class TestConfigValidationFailed:
    def test_event_type(self) -> None:
        event = ConfigValidationFailed(entry_id="e1", entry_key="k", errors=("invalid",))
        assert event.event_type == "configmgt.config.validation_failed"

    def test_fields(self) -> None:
        event = ConfigValidationFailed(entry_id="e1", entry_key="db.host", errors=("bad type",))
        assert event.entry_key == "db.host"
        assert event.errors == ("bad type",)


class TestConfigHotReloaded:
    def test_event_type(self) -> None:
        event = ConfigHotReloaded(changed_keys=("k1", "k2"))
        assert event.event_type == "configmgt.config.hot_reloaded"

    def test_fields(self) -> None:
        event = ConfigHotReloaded(changed_keys=("db.host", "db.port"), details={"count": 2})
        assert event.changed_keys == ("db.host", "db.port")
        assert event.details == {"count": 2}


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(ConfigCreated, DomainEvent)
        assert issubclass(ConfigUpdated, DomainEvent)
        assert issubclass(ConfigDeleted, DomainEvent)
        assert issubclass(ConfigProfileCreated, DomainEvent)
        assert issubclass(ConfigProfileApplied, DomainEvent)
        assert issubclass(ConfigSnapshotCreated, DomainEvent)
        assert issubclass(ConfigValidated, DomainEvent)
        assert issubclass(ConfigValidationFailed, DomainEvent)
        assert issubclass(ConfigHotReloaded, DomainEvent)
