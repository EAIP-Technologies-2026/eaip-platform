"""Tests for config backup Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from eaip.configbackup.models import (
    BackupConfig,
    ConfigSnapshot,
    RestorePoint,
    RestoreStatus,
    SnapshotStatus,
)


class TestConfigSnapshot:
    def test_default_values(self) -> None:
        snap = ConfigSnapshot(id="s1", resource_id="r1", config_type="json")
        assert snap.version == 1
        assert snap.data == {}
        assert snap.checksum == ""
        assert snap.status == SnapshotStatus.ACTIVE
        assert isinstance(snap.created_at, datetime)

    def test_frozen(self) -> None:
        snap = ConfigSnapshot(id="s1", resource_id="r1", config_type="json")
        with pytest.raises(ValidationError):
            snap.id = "s2"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ConfigSnapshot(id="s1", resource_id="r1", config_type="json", unknown=True)  # type: ignore[call-arg]

    def test_archived_status(self) -> None:
        snap = ConfigSnapshot(
            id="s1", resource_id="r1", config_type="json", status=SnapshotStatus.ARCHIVED
        )
        assert snap.status == SnapshotStatus.ARCHIVED


class TestRestorePoint:
    def test_default_values(self) -> None:
        rp = RestorePoint(id="rp1", snapshot_id="s1", restored_by="alice")
        assert rp.status == RestoreStatus.PENDING
        assert isinstance(rp.restored_at, datetime)

    def test_frozen(self) -> None:
        rp = RestorePoint(id="rp1", snapshot_id="s1", restored_by="alice")
        with pytest.raises(ValidationError):
            rp.status = RestoreStatus.COMPLETED  # type: ignore[misc]

    def test_completed_status(self) -> None:
        rp = RestorePoint(
            id="rp1", snapshot_id="s1", restored_by="alice", status=RestoreStatus.COMPLETED
        )
        assert rp.status == RestoreStatus.COMPLETED


class TestBackupConfig:
    def test_default_values(self) -> None:
        cfg = BackupConfig()
        assert cfg.max_snapshots_per_resource == 10
        assert cfg.enable_compression is False
        assert cfg.storage_backend == "memory"
        assert cfg.archive_after_days == 30

    def test_custom_values(self) -> None:
        cfg = BackupConfig(
            max_snapshots_per_resource=5,
            enable_compression=True,
            storage_backend="s3",
            archive_after_days=7,
        )
        assert cfg.max_snapshots_per_resource == 5
        assert cfg.archive_after_days == 7
