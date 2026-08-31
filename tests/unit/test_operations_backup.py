"""Tests for :mod:`eaip.operations.backup`."""

from __future__ import annotations

import pytest

from eaip.operations.backup import BackupManager
from eaip.operations.exceptions import BackupNotFoundError, BackupRestoreError
from eaip.operations.models import BackupComponent, BackupManifest


@pytest.fixture
def manager() -> BackupManager:
    return BackupManager()


@pytest.fixture
def sample_components() -> tuple[BackupComponent, ...]:
    return (
        BackupComponent(id="cfg-1", type="config", size_bytes=1024, record_count=10),
        BackupComponent(id="knw-1", type="knowledge", size_bytes=4096, record_count=50),
    )


class TestBackupManager:
    async def test_create_backup(self, manager: BackupManager) -> None:
        manifest = await manager.create_backup("test-backup")
        assert manifest.name == "test-backup"
        assert manifest.status == "completed"
        assert manifest.id.startswith("bkp-")

    async def test_create_backup_with_components(
        self, manager: BackupManager, sample_components: tuple[BackupComponent, ...]
    ) -> None:
        manifest = await manager.create_backup("full-backup", components=sample_components)
        assert len(manifest.components) == 2
        assert manifest.size_bytes == 5120

    async def test_get_backup(self, manager: BackupManager) -> None:
        created = await manager.create_backup("get-test")
        retrieved = await manager.get_backup(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    async def test_get_backup_not_found(self, manager: BackupManager) -> None:
        result = await manager.get_backup("does-not-exist")
        assert result is None

    async def test_list_backups(self, manager: BackupManager) -> None:
        await manager.create_backup("b1")
        await manager.create_backup("b2")
        backups = await manager.list_backups()
        assert len(backups) == 2

    async def test_list_backups_empty(self, manager: BackupManager) -> None:
        backups = await manager.list_backups()
        assert backups == []

    async def test_list_backups_by_component_type(
        self, manager: BackupManager, sample_components: tuple[BackupComponent, ...]
    ) -> None:
        await manager.create_backup("b1", components=sample_components)
        config_backups = await manager.list_backups(component_type="config")
        assert len(config_backups) == 1
        memory_backups = await manager.list_backups(component_type="memory")
        assert len(memory_backups) == 0

    async def test_delete_backup(self, manager: BackupManager) -> None:
        created = await manager.create_backup("delete-me")
        result = await manager.delete_backup(created.id)
        assert result is True
        assert await manager.get_backup(created.id) is None

    async def test_delete_backup_not_found(self, manager: BackupManager) -> None:
        with pytest.raises(BackupNotFoundError):
            await manager.delete_backup("does-not-exist")

    async def test_restore_backup(self, manager: BackupManager) -> None:
        created = await manager.create_backup("restore-me")
        restored = await manager.restore_backup(created.id)
        assert restored.id == created.id

    async def test_restore_backup_not_found(self, manager: BackupManager) -> None:
        with pytest.raises(BackupNotFoundError):
            await manager.restore_backup("does-not-exist")

    async def test_restore_failed_backup(self, manager: BackupManager) -> None:
        manifest = await manager.create_backup("fail-test")
        manager._backups[manifest.id] = BackupManifest(
            id=manifest.id,
            name=manifest.name,
            status="failed",
            started_at=manifest.started_at,
        )
        with pytest.raises(BackupRestoreError):
            await manager.restore_backup(manifest.id)

    async def test_verify_backup(self, manager: BackupManager) -> None:
        created = await manager.create_backup("verify-me")
        valid = await manager.verify_backup(created.id)
        assert valid is True

    async def test_verify_backup_not_found(self, manager: BackupManager) -> None:
        with pytest.raises(BackupNotFoundError):
            await manager.verify_backup("does-not-exist")

    async def test_create_backup_with_many_components(self, manager: BackupManager) -> None:
        comps = tuple(
            BackupComponent(id=f"c-{i}", type="config", size_bytes=100 * i) for i in range(5)
        )
        manifest = await manager.create_backup("multi", components=comps)
        assert len(manifest.components) == 5
        assert manifest.size_bytes == sum(100 * i for i in range(5))
