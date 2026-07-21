"""Tests for :mod:`eaip.operations.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.operations.models import (
    BackupComponent,
    BackupManifest,
    MaintenanceWindow,
    MigrationPlan,
    MigrationStep,
    OperationsConfig,
    SystemHealthSnapshot,
)


class TestMaintenanceWindow:
    def test_minimal(self) -> None:
        now = datetime.now(UTC)
        window = MaintenanceWindow(
            id="mw-1",
            name="Scheduled upgrade",
            scheduled_start=now,
            scheduled_end=now,
        )
        assert window.id == "mw-1"
        assert window.status == "scheduled"
        assert window.components == ()
        assert window.reason == ""

    def test_frozen(self) -> None:
        now = datetime.now(UTC)
        window = MaintenanceWindow(
            id="mw-1",
            name="test",
            scheduled_start=now,
            scheduled_end=now,
        )
        with pytest.raises(ValueError):
            window.name = "changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValueError):
            MaintenanceWindow(  # type: ignore[call-arg]
                id="mw-1",
                name="test",
                scheduled_start=now,
                scheduled_end=now,
                bad_key="x",
            )

    def test_with_all_fields(self) -> None:
        now = datetime.now(UTC)
        window = MaintenanceWindow(
            id="mw-2",
            name="DB migration",
            description="Migrate database schema",
            status="active",
            scheduled_start=now,
            scheduled_end=now,
            actual_start=now,
            actual_end=None,
            components=("db", "cache"),
            reason="Schema v2",
            created_by="admin",
            metadata={"ticket": "INC-123"},
            notify_users=("ops@example.com",),
        )
        assert window.status == "active"
        assert "db" in window.components
        assert window.metadata["ticket"] == "INC-123"
        assert window.notify_users == ("ops@example.com",)


class TestBackupComponent:
    def test_minimal(self) -> None:
        comp = BackupComponent(id="bc-1")
        assert comp.type == "config"
        assert comp.status == "pending"
        assert comp.size_bytes == 0

    def test_frozen(self) -> None:
        comp = BackupComponent(id="bc-1")
        with pytest.raises(ValueError):
            comp.type = "knowledge"  # type: ignore[misc]

    def test_with_all_fields(self) -> None:
        comp = BackupComponent(
            id="bc-2",
            type="knowledge",
            status="completed",
            size_bytes=4096,
            record_count=100,
            checksum="abc123",
            error="",
        )
        assert comp.type == "knowledge"
        assert comp.record_count == 100


class TestBackupManifest:
    def test_minimal(self) -> None:
        manifest = BackupManifest(id="bk-1", name="nightly")
        assert manifest.status == "in_progress"
        assert manifest.retention_days == 30
        assert isinstance(manifest.started_at, datetime)

    def test_frozen(self) -> None:
        manifest = BackupManifest(id="bk-1", name="test")
        with pytest.raises(ValueError):
            manifest.name = "changed"  # type: ignore[misc]

    def test_with_components(self) -> None:
        comp = BackupComponent(id="c1", type="config", status="completed", size_bytes=1024)
        manifest = BackupManifest(
            id="bk-2",
            name="full-backup",
            components=(comp,),
            status="completed",
            size_bytes=1024,
            checksum="xyz",
        )
        assert len(manifest.components) == 1
        assert manifest.components[0].id == "c1"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            BackupManifest(id="bk-1", name="test", unknown="x")  # type: ignore[call-arg]


class TestMigrationStep:
    def test_minimal(self) -> None:
        step = MigrationStep(id="ms-1")
        assert step.type == "data"
        assert step.status == "pending"
        assert step.duration_ms == 0.0

    def test_frozen(self) -> None:
        step = MigrationStep(id="ms-1")
        with pytest.raises(ValueError):
            step.status = "completed"  # type: ignore[misc]


class TestMigrationPlan:
    def test_minimal(self) -> None:
        plan = MigrationPlan(id="mp-1", name="upgrade", source_version="1.0", target_version="2.0")
        assert plan.status == "draft"
        assert isinstance(plan.created_at, datetime)

    def test_frozen(self) -> None:
        plan = MigrationPlan(id="mp-1", name="test", source_version="1.0", target_version="2.0")
        with pytest.raises(ValueError):
            plan.status = "completed"  # type: ignore[misc]

    def test_with_steps(self) -> None:
        step = MigrationStep(id="s1", description="Migrate data", type="data")
        plan = MigrationPlan(
            id="mp-2",
            name="v2 upgrade",
            source_version="1.0",
            target_version="2.0",
            steps=(step,),
            status="validated",
            metadata={"author": "admin"},
            rollback_plan="Reverse step order",
        )
        assert len(plan.steps) == 1
        assert plan.metadata["author"] == "admin"
        assert plan.rollback_plan == "Reverse step order"


class TestSystemHealthSnapshot:
    def test_minimal(self) -> None:
        snap = SystemHealthSnapshot(id="sh-1")
        assert snap.overall_status == "unknown"
        assert snap.metrics == {}
        assert snap.active_alerts == ()

    def test_frozen(self) -> None:
        snap = SystemHealthSnapshot(id="sh-1")
        with pytest.raises(ValueError):
            snap.overall_status = "healthy"  # type: ignore[misc]

    def test_with_all_fields(self) -> None:
        snap = SystemHealthSnapshot(
            id="sh-2",
            overall_status="degraded",
            component_statuses={"http": "healthy", "db": "degraded"},
            metrics={"cpu": 0.85, "memory": 0.6},
            active_alerts=("high-cpu",),
            version_info={"app": "1.0.0"},
            uptime_seconds=7200.0,
        )
        assert snap.component_statuses["db"] == "degraded"
        assert snap.metrics["cpu"] == 0.85
        assert snap.uptime_seconds == 7200.0


class TestOperationsConfig:
    def test_defaults(self) -> None:
        config = OperationsConfig()
        assert config.backup_retention_days == 30
        assert config.auto_backup_enabled is False
        assert config.health_check_interval_seconds == 60
        assert config.max_backup_size_bytes == 10_737_418_240

    def test_frozen(self) -> None:
        config = OperationsConfig()
        with pytest.raises(ValueError):
            config.backup_retention_days = 60  # type: ignore[misc]

    def test_custom_values(self) -> None:
        config = OperationsConfig(
            backup_retention_days=7,
            auto_backup_enabled=True,
            auto_backup_interval_hours=12,
            maintenance_approval_required=False,
            health_check_interval_seconds=30,
            max_backup_size_bytes=5_368_709_120,
        )
        assert config.backup_retention_days == 7
        assert config.auto_backup_enabled is True
        assert config.auto_backup_interval_hours == 12
        assert config.maintenance_approval_required is False
        assert config.health_check_interval_seconds == 30
        assert config.max_backup_size_bytes == 5_368_709_120
