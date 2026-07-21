"""Tests for configmgt models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.configmgt.models import (
    ConfigChange,
    ConfigEntry,
    ConfigEntrySource,
    ConfigEntryStatus,
    ConfigEntryType,
    ConfigMgtConfig,
    ConfigProfile,
    ConfigProfileStatus,
    ConfigSnapshot,
    ConfigValidation,
)


class TestConfigEntry:
    def test_minimal(self) -> None:
        e = ConfigEntry(id="e1", key="my.key", value="hello")
        assert e.type is ConfigEntryType.STRING
        assert e.source is ConfigEntrySource.MANUAL
        assert e.status is ConfigEntryStatus.ACTIVE
        assert e.version == 1
        assert e.tags == ()
        assert e.metadata == {}

    def test_frozen(self) -> None:
        e = ConfigEntry(id="e1", key="k", value="v")
        with pytest.raises(ValidationError):
            e.key = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ConfigEntry(id="e1", key="k", value="v", unknown=True)

    def test_all_types(self) -> None:
        for t in ConfigEntryType:
            e = ConfigEntry(id="e1", key="k", value="val", type=t)
            assert e.type is t

    def test_all_sources(self) -> None:
        for s in ConfigEntrySource:
            e = ConfigEntry(id="e1", key="k", value="v", source=s)
            assert e.source is s

    def test_all_statuses(self) -> None:
        for s in ConfigEntryStatus:
            e = ConfigEntry(id="e1", key="k", value="v", status=s)
            assert e.status is s

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        e = ConfigEntry(
            id="e1",
            key="db.host",
            value="localhost",
            type=ConfigEntryType.STRING,
            description="Database host",
            tags=("prod", "critical"),
            source=ConfigEntrySource.FILE,
            version=3,
            status=ConfigEntryStatus.ACTIVE,
            created_at=ts,
            updated_at=ts,
            metadata={"owner": "team-a"},
        )
        assert e.key == "db.host"
        assert e.description == "Database host"
        assert e.tags == ("prod", "critical")
        assert e.version == 3
        assert e.created_at == ts
        assert e.metadata == {"owner": "team-a"}


class TestConfigProfile:
    def test_minimal(self) -> None:
        p = ConfigProfile(id="p1", name="Production")
        assert p.environment == ""
        assert p.entries == {}
        assert p.parent_profile is None
        assert p.status is ConfigProfileStatus.ACTIVE

    def test_frozen(self) -> None:
        p = ConfigProfile(id="p1", name="P1")
        with pytest.raises(ValidationError):
            p.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ConfigProfile(id="p1", name="P1", unknown=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        p = ConfigProfile(
            id="p1",
            name="Production",
            environment="prod",
            entries={"db.host": "prod-db.example.com"},
            parent_profile="base",
            status=ConfigProfileStatus.INACTIVE,
            created_at=ts,
            updated_at=ts,
            metadata={"owner": "team-a"},
        )
        assert p.environment == "prod"
        assert p.entries == {"db.host": "prod-db.example.com"}
        assert p.parent_profile == "base"
        assert p.status is ConfigProfileStatus.INACTIVE


class TestConfigChange:
    def test_minimal(self) -> None:
        c = ConfigChange(id="chg1", entry_id="e1")
        assert c.old_value == ""
        assert c.new_value == ""
        assert c.changed_by == ""
        assert c.reason == ""

    def test_frozen(self) -> None:
        c = ConfigChange(id="chg1", entry_id="e1")
        with pytest.raises(ValidationError):
            c.entry_id = "changed"

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        c = ConfigChange(
            id="chg1",
            entry_id="e1",
            old_value="localhost",
            new_value="newhost",
            changed_by="admin",
            reason="host migration",
            timestamp=ts,
            metadata={"ticket": "INC-123"},
        )
        assert c.old_value == "localhost"
        assert c.new_value == "newhost"
        assert c.changed_by == "admin"
        assert c.reason == "host migration"
        assert c.metadata == {"ticket": "INC-123"}


class TestConfigValidation:
    def test_minimal(self) -> None:
        v = ConfigValidation(id="val1", entry_id="e1")
        assert v.valid is True
        assert v.errors == ()
        assert v.warnings == ()

    def test_invalid(self) -> None:
        v = ConfigValidation(id="val1", entry_id="e1", valid=False, errors=("bad value",))
        assert v.valid is False
        assert v.errors == ("bad value",)

    def test_full(self) -> None:
        v = ConfigValidation(
            id="val1",
            entry_id="e1",
            valid=False,
            errors=("err1",),
            warnings=("warn1",),
            metadata={"rule": "not_null"},
        )
        assert v.errors == ("err1",)
        assert v.warnings == ("warn1",)


class TestConfigSnapshot:
    def test_minimal(self) -> None:
        s = ConfigSnapshot(id="snap1", profile_id="p1")
        assert s.entries == {}
        assert s.checksum == ""

    def test_frozen(self) -> None:
        s = ConfigSnapshot(id="snap1", profile_id="p1")
        with pytest.raises(ValidationError):
            s.profile_id = "changed"


class TestConfigMgtConfig:
    def test_defaults(self) -> None:
        c = ConfigMgtConfig()
        assert c.enable_audit_logging is True
        assert c.enable_versioning is True
        assert c.cache_ttl_seconds == 300
        assert c.max_snapshots == 50
        assert c.enable_hot_reload is True
        assert c.validation_on_update is True

    def test_custom(self) -> None:
        c = ConfigMgtConfig(
            enable_audit_logging=False,
            enable_versioning=False,
            cache_ttl_seconds=600,
            max_snapshots=10,
            enable_hot_reload=False,
            validation_on_update=False,
        )
        assert c.enable_audit_logging is False
        assert c.cache_ttl_seconds == 600
        assert c.max_snapshots == 10

    def test_frozen(self) -> None:
        c = ConfigMgtConfig()
        with pytest.raises(ValidationError):
            c.enable_audit_logging = False
