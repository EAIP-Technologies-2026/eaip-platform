"""Domain events for platform lifecycle management."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent
from eaip.platform_lifecycle.models import (
    ComponentStatus,
    PlatformLifecyclePhase,
)


class PlatformLifecyclePhaseChanged(DomainEvent):
    """Emitted when the platform lifecycle phase changes."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.phase.changed"

    previous_phase: PlatformLifecyclePhase
    new_phase: PlatformLifecyclePhase


class PlatformLifecycleStateTransitioned(DomainEvent):
    """Emitted when the platform undergoes a state transition."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.state.transitioned"

    transition_id: str
    from_phase: PlatformLifecyclePhase
    to_phase: PlatformLifecyclePhase
    reason: str = Field(default="")


class PlatformUpgradeStarted(DomainEvent):
    """Emitted when a platform upgrade starts."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.upgrade.started"

    upgrade_id: str
    from_version: str
    to_version: str


class PlatformUpgradeCompleted(DomainEvent):
    """Emitted when a platform upgrade completes successfully."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.upgrade.completed"

    upgrade_id: str
    from_version: str
    to_version: str


class PlatformUpgradeFailed(DomainEvent):
    """Emitted when a platform upgrade fails."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.upgrade.failed"

    upgrade_id: str
    from_version: str
    to_version: str
    reason: str


class PlatformUpgradeRolledBack(DomainEvent):
    """Emitted when a platform upgrade is rolled back."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.upgrade.rolled_back"

    upgrade_id: str
    from_version: str
    to_version: str
    reason: str


class PlatformMigrationStarted(DomainEvent):
    """Emitted when a platform migration starts."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.migration.started"

    migration_id: str
    from_environment: str
    to_environment: str


class PlatformMigrationCompleted(DomainEvent):
    """Emitted when a platform migration completes successfully."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.migration.completed"

    migration_id: str
    from_environment: str
    to_environment: str


class PlatformMigrationFailed(DomainEvent):
    """Emitted when a platform migration fails."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.migration.failed"

    migration_id: str
    from_environment: str
    to_environment: str
    reason: str


class PlatformMigrationRolledBack(DomainEvent):
    """Emitted when a platform migration is rolled back."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.migration.rolled_back"

    migration_id: str
    from_environment: str
    to_environment: str
    reason: str


class PlatformHealthSummaryGenerated(DomainEvent):
    """Emitted when a platform health summary is generated."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.health_summary.generated"

    total_components: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    offline_count: int


class PlatformComponentStatusChanged(DomainEvent):
    """Emitted when a component's status changes."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.component.status_changed"

    component_id: str
    component_name: str
    previous_status: ComponentStatus
    new_status: ComponentStatus


class PlatformLifecyclePolicyApplied(DomainEvent):
    """Emitted when a lifecycle policy is applied."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.policy.applied"

    policy_id: str
    policy_name: str


class PlatformMaintenanceWindowStarted(DomainEvent):
    """Emitted when a maintenance window starts."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.maintenance_window.started"

    window_id: str
    description: str
    scheduled_start: datetime
    scheduled_end: datetime


class PlatformMaintenanceWindowEnded(DomainEvent):
    """Emitted when a maintenance window ends."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.maintenance_window.ended"

    window_id: str
    description: str
    actual_start: datetime
    actual_end: datetime


class PlatformDeprecationNoticeIssued(DomainEvent):
    """Emitted when a deprecation notice is issued."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.deprecation_notice.issued"

    notice_id: str
    component: str
    message: str
    deprecation_date: datetime
    removal_date: datetime | None = Field(default=None)


class PlatformLifecycleReportGenerated(DomainEvent):
    """Emitted when a lifecycle report is generated."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.report.generated"

    report_id: str
    report_type: str


class PlatformLifecycleAuditLogged(DomainEvent):
    """Emitted when a lifecycle audit entry is logged."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.audit.logged"

    entry_id: str
    action: str
    actor: str


class PlatformVersionUpdated(DomainEvent):
    """Emitted when the platform version is updated."""

    event_type: ClassVar[str] = "eaip.platform_lifecycle.version.updated"

    version: str
    build: str = Field(default="")


__all__ = [
    "PlatformComponentStatusChanged",
    "PlatformDeprecationNoticeIssued",
    "PlatformHealthSummaryGenerated",
    "PlatformLifecycleAuditLogged",
    "PlatformLifecyclePhaseChanged",
    "PlatformLifecyclePolicyApplied",
    "PlatformLifecycleReportGenerated",
    "PlatformLifecycleStateTransitioned",
    "PlatformMaintenanceWindowEnded",
    "PlatformMaintenanceWindowStarted",
    "PlatformMigrationCompleted",
    "PlatformMigrationFailed",
    "PlatformMigrationRolledBack",
    "PlatformMigrationStarted",
    "PlatformUpgradeCompleted",
    "PlatformUpgradeFailed",
    "PlatformUpgradeRolledBack",
    "PlatformUpgradeStarted",
    "PlatformVersionUpdated",
]
