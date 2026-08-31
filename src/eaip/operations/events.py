"""Domain events raised by the operations package."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class MaintenanceScheduled(DomainEvent):
    """Published when a maintenance window is scheduled."""

    event_type: ClassVar[str] = "eaip.operations.maintenance_scheduled"

    window_id: str
    name: str
    scheduled_start: datetime
    scheduled_end: datetime
    reason: str = ""
    created_by: str = "system"


class MaintenanceStarted(DomainEvent):
    """Published when a maintenance window starts."""

    event_type: ClassVar[str] = "eaip.operations.maintenance_started"

    window_id: str
    name: str
    actual_start: datetime


class MaintenanceCompleted(DomainEvent):
    """Published when a maintenance window completes."""

    event_type: ClassVar[str] = "eaip.operations.maintenance_completed"

    window_id: str
    name: str
    actual_end: datetime
    status: str = "completed"


class BackupCreated(DomainEvent):
    """Published when a backup is created."""

    event_type: ClassVar[str] = "eaip.operations.backup_created"

    backup_id: str
    name: str
    components: tuple[str, ...] = Field(default=())
    size_bytes: int = 0


class BackupRestored(DomainEvent):
    """Published when a backup is restored."""

    event_type: ClassVar[str] = "eaip.operations.backup_restored"

    backup_id: str
    name: str
    restored_at: datetime | None = None


class BackupVerified(DomainEvent):
    """Published when a backup integrity check completes."""

    event_type: ClassVar[str] = "eaip.operations.backup_verified"

    backup_id: str
    verified: bool
    checksum_match: bool = True


class MigrationCreated(DomainEvent):
    """Published when a migration plan is created."""

    event_type: ClassVar[str] = "eaip.operations.migration_created"

    plan_id: str
    name: str
    source_version: str
    target_version: str


class MigrationStarted(DomainEvent):
    """Published when a migration begins execution."""

    event_type: ClassVar[str] = "eaip.operations.migration_started"

    plan_id: str
    name: str
    step_count: int = 0


class MigrationCompleted(DomainEvent):
    """Published when a migration completes successfully."""

    event_type: ClassVar[str] = "eaip.operations.migration_completed"

    plan_id: str
    name: str
    completed_at: datetime | None = None


class MigrationRolledBack(DomainEvent):
    """Published when a migration is rolled back."""

    event_type: ClassVar[str] = "eaip.operations.migration_rolled_back"

    plan_id: str
    name: str
    reason: str = ""


class HealthSnapshotCaptured(DomainEvent):
    """Published when a health snapshot is captured."""

    event_type: ClassVar[str] = "eaip.operations.health_snapshot_captured"

    snapshot_id: str
    overall_status: str
    component_count: int = 0


class ComponentHealthChanged(DomainEvent):
    """Published when a component's health status changes."""

    event_type: ClassVar[str] = "eaip.operations.component_health_changed"

    component: str
    previous_status: str
    current_status: str
    message: str = ""


__all__ = [
    "BackupCreated",
    "BackupRestored",
    "BackupVerified",
    "ComponentHealthChanged",
    "HealthSnapshotCaptured",
    "MaintenanceCompleted",
    "MaintenanceScheduled",
    "MaintenanceStarted",
    "MigrationCompleted",
    "MigrationCreated",
    "MigrationRolledBack",
    "MigrationStarted",
]
