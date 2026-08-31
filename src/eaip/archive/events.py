"""Domain events for the archival subsystem."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ArchiveCreated(DomainEvent):
    """Emitted when a new archive record is created."""

    event_type: ClassVar[str] = "eaip.archive.created"
    record_id: str = ""
    source_collection: str = ""
    size_bytes: int = 0


class ArchiveRestored(DomainEvent):
    """Emitted when an archived record is restored."""

    event_type: ClassVar[str] = "eaip.archive.restored"
    record_id: str = ""
    target_collection: str = ""


class ArchivePruned(DomainEvent):
    """Emitted when archived records are pruned by a retention policy."""

    event_type: ClassVar[str] = "eaip.archive.pruned"
    policy_id: str = ""
    items_removed: int = 0
    bytes_freed: int = 0


class RetentionPolicyApplied(DomainEvent):
    """Emitted when a retention policy has been evaluated and applied."""

    event_type: ClassVar[str] = "eaip.archive.retention_policy_applied"
    policy_id: str = ""
    affected_items: int = 0


class ArchiveFailed(DomainEvent):
    """Emitted when an archival operation fails."""

    event_type: ClassVar[str] = "eaip.archive.failed"
    record_id: str = ""
    error_message: str = ""
    source_collection: str = ""


ArchiveEvent = (
    ArchiveCreated | ArchiveRestored | ArchivePruned | RetentionPolicyApplied | ArchiveFailed
)


__all__ = [
    "ArchiveCreated",
    "ArchiveEvent",
    "ArchiveFailed",
    "ArchivePruned",
    "ArchiveRestored",
    "RetentionPolicyApplied",
]
