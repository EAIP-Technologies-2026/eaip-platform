"""Configuration backup service — snapshot, restore, and archive configs."""

from __future__ import annotations

from eaip.configbackup.models import (
    BackupConfig,
    ConfigSnapshot,
    RestorePoint,
    RestoreStatus,
    SnapshotStatus,
)
from eaip.logging.context import get_logger


class ConfigBackupService:
    """Service for managing configuration snapshots and restore points."""

    def __init__(self, config: BackupConfig | None = None) -> None:
        self._config = config or BackupConfig()
        self._snapshots: dict[str, ConfigSnapshot] = {}
        self._restore_points: dict[str, RestorePoint] = {}
        self._log = get_logger("eaip.configbackup.service")

    @property
    def config(self) -> BackupConfig:
        return self._config

    async def create_snapshot(self, snapshot: ConfigSnapshot) -> ConfigSnapshot:
        self._snapshots[snapshot.id] = snapshot
        self._log.info(
            "snapshot.created", snapshot_id=snapshot.id, resource_id=snapshot.resource_id
        )
        return snapshot

    async def get_snapshot(self, snapshot_id: str) -> ConfigSnapshot | None:
        return self._snapshots.get(snapshot_id)

    async def list_snapshots(self, resource_id: str) -> list[ConfigSnapshot]:
        return [s for s in self._snapshots.values() if s.resource_id == resource_id]

    async def archive_snapshot(self, snapshot_id: str) -> ConfigSnapshot | None:
        snap = self._snapshots.get(snapshot_id)
        if snap is None:
            return None
        archived = ConfigSnapshot(
            id=snap.id,
            resource_id=snap.resource_id,
            config_type=snap.config_type,
            data=snap.data,
            checksum=snap.checksum,
            version=snap.version,
            created_at=snap.created_at,
            status=SnapshotStatus.ARCHIVED,
        )
        self._snapshots[snapshot_id] = archived
        return archived

    async def create_restore_point(self, restore: RestorePoint) -> RestorePoint:
        self._restore_points[restore.id] = restore
        self._log.info("restore.created", restore_id=restore.id, snapshot_id=restore.snapshot_id)
        return restore

    async def complete_restore(self, restore_id: str) -> RestorePoint | None:
        rp = self._restore_points.get(restore_id)
        if rp is None:
            return None
        completed = RestorePoint(
            id=rp.id,
            snapshot_id=rp.snapshot_id,
            restored_at=rp.restored_at,
            restored_by=rp.restored_by,
            status=RestoreStatus.COMPLETED,
        )
        self._restore_points[restore_id] = completed
        return completed
