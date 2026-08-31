"""Tests for ConfigBackupService."""

from __future__ import annotations

import pytest

from eaip.configbackup.models import (
    BackupConfig,
    ConfigSnapshot,
    RestorePoint,
    RestoreStatus,
    SnapshotStatus,
)
from eaip.configbackup.service import ConfigBackupService


class TestConfigBackupService:
    @pytest.mark.asyncio
    async def test_create_snapshot(self) -> None:
        svc = ConfigBackupService()
        snap = ConfigSnapshot(id="s1", resource_id="r1", config_type="json", data={"key": "val"})
        result = await svc.create_snapshot(snap)
        assert result.id == "s1"
        assert result.data == {"key": "val"}

    @pytest.mark.asyncio
    async def test_get_snapshot_found(self) -> None:
        svc = ConfigBackupService()
        snap = ConfigSnapshot(id="s1", resource_id="r1", config_type="json")
        await svc.create_snapshot(snap)
        result = await svc.get_snapshot("s1")
        assert result is not None
        assert result.id == "s1"

    @pytest.mark.asyncio
    async def test_get_snapshot_not_found(self) -> None:
        svc = ConfigBackupService()
        result = await svc.get_snapshot("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_snapshots(self) -> None:
        svc = ConfigBackupService()
        await svc.create_snapshot(ConfigSnapshot(id="s1", resource_id="r1", config_type="json"))
        await svc.create_snapshot(ConfigSnapshot(id="s2", resource_id="r1", config_type="yaml"))
        await svc.create_snapshot(ConfigSnapshot(id="s3", resource_id="r2", config_type="json"))
        snapshots = await svc.list_snapshots("r1")
        assert len(snapshots) == 2

    @pytest.mark.asyncio
    async def test_archive_snapshot(self) -> None:
        svc = ConfigBackupService()
        snap = ConfigSnapshot(id="s1", resource_id="r1", config_type="json")
        await svc.create_snapshot(snap)
        archived = await svc.archive_snapshot("s1")
        assert archived is not None
        assert archived.status == SnapshotStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_archive_snapshot_not_found(self) -> None:
        svc = ConfigBackupService()
        result = await svc.archive_snapshot("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_restore_point(self) -> None:
        svc = ConfigBackupService()
        snap = ConfigSnapshot(id="s1", resource_id="r1", config_type="json")
        await svc.create_snapshot(snap)
        rp = RestorePoint(id="rp1", snapshot_id="s1", restored_by="alice")
        result = await svc.create_restore_point(rp)
        assert result.id == "rp1"
        assert result.status == RestoreStatus.PENDING

    @pytest.mark.asyncio
    async def test_complete_restore(self) -> None:
        svc = ConfigBackupService()
        snap = ConfigSnapshot(id="s1", resource_id="r1", config_type="json")
        await svc.create_snapshot(snap)
        rp = RestorePoint(id="rp1", snapshot_id="s1", restored_by="alice")
        await svc.create_restore_point(rp)
        completed = await svc.complete_restore("rp1")
        assert completed is not None
        assert completed.status == RestoreStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_config(self) -> None:
        cfg = BackupConfig(max_snapshots_per_resource=5)
        svc = ConfigBackupService(config=cfg)
        assert svc.config.max_snapshots_per_resource == 5
