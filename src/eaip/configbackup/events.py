"""Domain events emitted by the configuration backup service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class SnapshotCreated(DomainEvent):
    """Emitted when a configuration snapshot is created."""

    event_type: ClassVar[str] = "eaip.configbackup.snapshot_created"

    snapshot_id: str
    resource_id: str
    version: int


class SnapshotRestored(DomainEvent):
    """Emitted when a configuration snapshot is restored."""

    event_type: ClassVar[str] = "eaip.configbackup.snapshot_restored"

    restore_id: str
    snapshot_id: str
    restored_by: str


class SnapshotArchived(DomainEvent):
    """Emitted when a configuration snapshot is archived."""

    event_type: ClassVar[str] = "eaip.configbackup.snapshot_archived"

    snapshot_id: str
    resource_id: str
