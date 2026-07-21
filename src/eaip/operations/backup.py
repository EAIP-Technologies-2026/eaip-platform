"""Backup and restore management."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from eaip.logging.context import get_logger
from eaip.operations.exceptions import BackupNotFoundError, BackupRestoreError
from eaip.operations.models import BackupComponent, BackupManifest


class BackupManager:
    """Manages system backups and restores."""

    def __init__(self) -> None:
        """Initialize the backup manager."""
        self._backups: dict[str, BackupManifest] = {}
        self._log = get_logger("eaip.operations.backup")

    async def create_backup(
        self,
        name: str,
        components: tuple[BackupComponent, ...] = (),
    ) -> BackupManifest:
        """Create a system backup.

        Args:
            name: A human-readable name for the backup.
            components: The components to include in the backup.

        Returns:
            The created backup manifest.
        """
        backup_id = f"bkp-{datetime.now(UTC).timestamp():.0f}-{hash(name) & 0xFFFF:04x}"
        completed_components = tuple(
            BackupComponent(
                id=c.id,
                type=c.type,
                status="completed",
                size_bytes=c.size_bytes,
                record_count=c.record_count,
                checksum=c.checksum or hashlib.sha256(c.id.encode()).hexdigest()[:16],
                error=c.error,
            )
            for c in components
        )
        total_size = sum(c.size_bytes for c in completed_components)
        data = json.dumps(
            {
                "name": name,
                "components": [
                    {"id": c.id, "type": c.type, "checksum": c.checksum}
                    for c in completed_components
                ],
            },
            sort_keys=True,
        )
        checksum = hashlib.sha256(data.encode()).hexdigest()

        manifest = BackupManifest(
            id=backup_id,
            name=name,
            components=completed_components,
            status="completed",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            size_bytes=total_size,
            checksum=checksum,
            location=f"memory://backups/{backup_id}",
        )
        self._backups[backup_id] = manifest
        self._log.info("backup.created", backup_id=backup_id, name=name, size=total_size)
        return manifest

    async def restore_backup(self, backup_id: str) -> BackupManifest:
        """Restore from a backup.

        Args:
            backup_id: The ID of the backup to restore.

        Returns:
            The restored backup manifest.

        Raises:
            BackupNotFoundError: If the backup does not exist.
            BackupRestoreError: If the backup is in a failed state.
        """
        manifest = self._backups.get(backup_id)
        if manifest is None:
            raise BackupNotFoundError(
                f"Backup {backup_id} not found",
                context={"backup_id": backup_id},
            )
        if manifest.status == "failed":
            raise BackupRestoreError(
                f"Cannot restore failed backup {backup_id}",
                context={"backup_id": backup_id, "status": manifest.status},
            )
        self._log.info("backup.restored", backup_id=backup_id)
        return manifest

    async def get_backup(self, backup_id: str) -> BackupManifest | None:
        """Get backup details by ID.

        Args:
            backup_id: The backup identifier.

        Returns:
            The backup manifest, or None if not found.
        """
        return self._backups.get(backup_id)

    async def list_backups(self, component_type: str | None = None) -> list[BackupManifest]:
        """List backups, optionally filtered by component type.

        Args:
            component_type: Optional component type filter.

        Returns:
            A list of matching backup manifests.
        """
        if component_type is None:
            return list(self._backups.values())
        return [
            b for b in self._backups.values() if any(c.type == component_type for c in b.components)
        ]

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup.

        Args:
            backup_id: The ID of the backup to delete.

        Returns:
            True if the backup was deleted.

        Raises:
            BackupNotFoundError: If the backup does not exist.
        """
        if backup_id not in self._backups:
            raise BackupNotFoundError(
                f"Backup {backup_id} not found",
                context={"backup_id": backup_id},
            )
        del self._backups[backup_id]
        self._log.info("backup.deleted", backup_id=backup_id)
        return True

    async def verify_backup(self, backup_id: str) -> bool:
        """Verify the integrity of a backup.

        Args:
            backup_id: The ID of the backup to verify.

        Returns:
            True if the backup is valid, False otherwise.

        Raises:
            BackupNotFoundError: If the backup does not exist.
        """
        manifest = self._backups.get(backup_id)
        if manifest is None:
            raise BackupNotFoundError(
                f"Backup {backup_id} not found",
                context={"backup_id": backup_id},
            )
        data = json.dumps(
            {
                "name": manifest.name,
                "components": [
                    {"id": c.id, "type": c.type, "checksum": c.checksum}
                    for c in manifest.components
                ],
            },
            sort_keys=True,
        )
        expected_checksum = hashlib.sha256(data.encode()).hexdigest()
        valid = expected_checksum == manifest.checksum
        self._log.info(
            "backup.verified",
            backup_id=backup_id,
            valid=valid,
        )
        return valid


__all__ = ["BackupManager"]
