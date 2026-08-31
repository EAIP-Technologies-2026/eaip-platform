"""Domain events for backup verification."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class BackupRecorded(DomainEvent):
    """Emitted when a new backup is recorded."""

    event_type: ClassVar[str] = "eaip.backupver.backup.recorded"

    record_id: str
    resource_id: str
    backup_type: str
    size_bytes: int


class BackupVerified(DomainEvent):
    """Emitted when a backup verification completes."""

    event_type: ClassVar[str] = "eaip.backupver.backup.verified"

    record_id: str
    integrity_pass: bool
    duration_ms: int


class BackupRecoveryTested(DomainEvent):
    """Emitted when a backup recovery test completes."""

    event_type: ClassVar[str] = "eaip.backupver.backup.recovery_tested"

    record_id: str
    recovery_test_pass: bool
    duration_ms: int


__all__ = [
    "BackupRecorded",
    "BackupRecoveryTested",
    "BackupVerified",
]
