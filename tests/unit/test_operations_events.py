"""Tests for :mod:`eaip.operations.events`."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.events.event import DomainEvent
from eaip.operations.events import (
    BackupCreated,
    BackupRestored,
    BackupVerified,
    ComponentHealthChanged,
    HealthSnapshotCaptured,
    MaintenanceCompleted,
    MaintenanceScheduled,
    MaintenanceStarted,
    MigrationCompleted,
    MigrationCreated,
    MigrationRolledBack,
    MigrationStarted,
)


class TestMaintenanceEvents:
    def test_maintenance_scheduled(self) -> None:
        now = datetime.now()
        event = MaintenanceScheduled(
            window_id="mw-1",
            name="Upgrade",
            scheduled_start=now,
            scheduled_end=now,
        )
        assert event.event_type == "eaip.operations.maintenance_scheduled"
        assert isinstance(event, DomainEvent)
        assert event.window_id == "mw-1"

    def test_maintenance_started(self) -> None:
        now = datetime.now()
        event = MaintenanceStarted(
            window_id="mw-1",
            name="Upgrade",
            actual_start=now,
        )
        assert event.event_type == "eaip.operations.maintenance_started"
        assert event.actual_start == now

    def test_maintenance_completed(self) -> None:
        now = datetime.now()
        event = MaintenanceCompleted(
            window_id="mw-1",
            name="Upgrade",
            actual_end=now,
            status="completed",
        )
        assert event.event_type == "eaip.operations.maintenance_completed"


class TestBackupEvents:
    def test_backup_created(self) -> None:
        event = BackupCreated(
            backup_id="bkp-1",
            name="nightly",
            components=("config", "knowledge"),
            size_bytes=4096,
        )
        assert event.event_type == "eaip.operations.backup_created"
        assert event.backup_id == "bkp-1"
        assert len(event.components) == 2

    def test_backup_restored(self) -> None:
        event = BackupRestored(backup_id="bkp-1", name="nightly")
        assert event.event_type == "eaip.operations.backup_restored"
        assert event.restored_at is None

    def test_backup_verified(self) -> None:
        event = BackupVerified(backup_id="bkp-1", verified=True)
        assert event.event_type == "eaip.operations.backup_verified"
        assert event.verified is True
        assert event.checksum_match is True

    def test_backup_verified_failed(self) -> None:
        event = BackupVerified(backup_id="bkp-1", verified=False, checksum_match=False)
        assert event.verified is False
        assert event.checksum_match is False


class TestMigrationEvents:
    def test_migration_created(self) -> None:
        event = MigrationCreated(
            plan_id="mp-1",
            name="v2 upgrade",
            source_version="1.0",
            target_version="2.0",
        )
        assert event.event_type == "eaip.operations.migration_created"
        assert event.source_version == "1.0"

    def test_migration_started(self) -> None:
        event = MigrationStarted(plan_id="mp-1", name="v2 upgrade", step_count=3)
        assert event.event_type == "eaip.operations.migration_started"
        assert event.step_count == 3

    def test_migration_completed(self) -> None:
        event = MigrationCompleted(plan_id="mp-1", name="v2 upgrade")
        assert event.event_type == "eaip.operations.migration_completed"
        assert event.completed_at is None

    def test_migration_rolled_back(self) -> None:
        event = MigrationRolledBack(plan_id="mp-1", name="v2 upgrade", reason="data issue")
        assert event.event_type == "eaip.operations.migration_rolled_back"
        assert event.reason == "data issue"


class TestHealthEvents:
    def test_health_snapshot_captured(self) -> None:
        event = HealthSnapshotCaptured(
            snapshot_id="snap-1",
            overall_status="healthy",
            component_count=5,
        )
        assert event.event_type == "eaip.operations.health_snapshot_captured"
        assert event.component_count == 5

    def test_component_health_changed(self) -> None:
        event = ComponentHealthChanged(
            component="db",
            previous_status="healthy",
            current_status="degraded",
            message="Connection pool exhausted",
        )
        assert event.event_type == "eaip.operations.component_health_changed"
        assert event.message == "Connection pool exhausted"


class TestEventCommon:
    def test_events_are_frozen(self) -> None:
        event = BackupCreated(backup_id="b-1", name="test")
        with pytest.raises(ValueError):
            event.backup_id = "other"  # type: ignore[misc]

    def test_events_have_occurred_at(self) -> None:
        event = MaintenanceScheduled(
            window_id="mw-1",
            name="test",
            scheduled_start=datetime.now(),
            scheduled_end=datetime.now(),
        )
        assert isinstance(event.occurred_at, datetime)
