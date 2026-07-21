"""Data models for platform lifecycle management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PlatformLifecyclePhase(StrEnum):
    """Enumeration of platform lifecycle phases."""

    CREATED = "created"
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    UPGRADING = "upgrading"
    MIGRATING = "migrating"
    ARCHIVED = "archived"


class PlatformUpgradeStatus(StrEnum):
    """Status of a platform upgrade operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class PlatformMigrationStatus(StrEnum):
    """Status of a platform migration operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ComponentStatus(StrEnum):
    """Health status of a platform component."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class PlatformLifecycleState(BaseModel):
    """Overall lifecycle state of the platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    phase: PlatformLifecyclePhase
    previous_phase: PlatformLifecyclePhase | None = Field(default=None)
    started_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    message: str = Field(default="")


class PlatformLifecycleTransition(BaseModel):
    """A recorded transition between lifecycle phases."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    from_phase: PlatformLifecyclePhase
    to_phase: PlatformLifecyclePhase
    timestamp: datetime = Field(default_factory=utc_now)
    reason: str = Field(default="")
    triggered_by: str = Field(default="")


class PlatformUpgrade(BaseModel):
    """A platform upgrade operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    from_version: str
    to_version: str
    status: PlatformUpgradeStatus = Field(default=PlatformUpgradeStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    message: str = Field(default="")
    metadata: dict[str, str] = Field(default_factory=dict)


class PlatformMigration(BaseModel):
    """A platform migration operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    from_environment: str
    to_environment: str
    status: PlatformMigrationStatus = Field(default=PlatformMigrationStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    message: str = Field(default="")
    metadata: dict[str, str] = Field(default_factory=dict)


class PlatformHealthSummary(BaseModel):
    """Health summary for the platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    overall_status: str = Field(default="healthy")
    total_components: int = Field(default=0)
    healthy_count: int = Field(default=0)
    degraded_count: int = Field(default=0)
    unhealthy_count: int = Field(default=0)
    offline_count: int = Field(default=0)
    generated_at: datetime = Field(default_factory=utc_now)


class PlatformComponent(BaseModel):
    """A component tracked by the platform lifecycle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    status: ComponentStatus = Field(default=ComponentStatus.HEALTHY)
    version: str = Field(default="")
    last_checked: datetime | None = Field(default=None)
    metadata: dict[str, str] = Field(default_factory=dict)


class PlatformLifecycleConfig(BaseModel):
    """Configuration for platform lifecycle management."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    health_check_interval_seconds: int = Field(default=60, ge=1)
    auto_rollback_enabled: bool = Field(default=True)
    max_upgrade_attempts: int = Field(default=3, ge=1)
    max_migration_attempts: int = Field(default=3, ge=1)
    audit_retention_days: int = Field(default=365, ge=1)


class PlatformLifecycleEvent(BaseModel):
    """A recorded lifecycle event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    event_type: str
    timestamp: datetime = Field(default_factory=utc_now)
    data: dict[str, str] = Field(default_factory=dict)


class PlatformLifecyclePolicy(BaseModel):
    """A lifecycle policy rule."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    enabled: bool = Field(default=True)
    rules: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class PlatformLifecycleSchedule(BaseModel):
    """A scheduled lifecycle operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    operation: str
    cron_expression: str
    enabled: bool = Field(default=True)
    last_run: datetime | None = Field(default=None)
    next_run: datetime | None = Field(default=None)
    metadata: dict[str, str] = Field(default_factory=dict)


class PlatformLifecycleAuditEntry(BaseModel):
    """An audit trail entry for lifecycle operations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    action: str
    actor: str = Field(default="system")
    timestamp: datetime = Field(default_factory=utc_now)
    details: str = Field(default="")
    data: dict[str, str] = Field(default_factory=dict)


class PlatformLifecycleReport(BaseModel):
    """A generated lifecycle report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    report_type: str
    generated_at: datetime = Field(default_factory=utc_now)
    period_start: datetime | None = Field(default=None)
    period_end: datetime | None = Field(default=None)
    summary: str = Field(default="")
    data: dict[str, str] = Field(default_factory=dict)


class PlatformVersionInfo(BaseModel):
    """Version information for the platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    build: str = Field(default="")
    release_date: datetime | None = Field(default=None)
    changelog: str = Field(default="")
    metadata: dict[str, str] = Field(default_factory=dict)


class PlatformDeprecationNotice(BaseModel):
    """A deprecation notice for a platform feature or component."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    component: str
    message: str
    deprecation_date: datetime
    removal_date: datetime | None = Field(default=None)
    migration_guide: str = Field(default="")
    issued_at: datetime = Field(default_factory=utc_now)


class PlatformMaintenanceWindow(BaseModel):
    """A scheduled maintenance window."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    description: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: datetime | None = Field(default=None)
    actual_end: datetime | None = Field(default=None)
    status: str = Field(default="scheduled")
    metadata: dict[str, str] = Field(default_factory=dict)


class PlatformLifecycleDashboard(BaseModel):
    """Dashboard data summarizing the platform lifecycle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    current_phase: PlatformLifecyclePhase
    overall_health: str = Field(default="healthy")
    active_upgrades: int = Field(default=0)
    active_migrations: int = Field(default=0)
    active_maintenance_windows: int = Field(default=0)
    component_count: int = Field(default=0)
    unhealthy_components: int = Field(default=0)
    last_updated: datetime = Field(default_factory=utc_now)


__all__ = [
    "ComponentStatus",
    "PlatformComponent",
    "PlatformDeprecationNotice",
    "PlatformHealthSummary",
    "PlatformLifecycleAuditEntry",
    "PlatformLifecycleConfig",
    "PlatformLifecycleDashboard",
    "PlatformLifecycleEvent",
    "PlatformLifecyclePhase",
    "PlatformLifecyclePolicy",
    "PlatformLifecycleReport",
    "PlatformLifecycleSchedule",
    "PlatformLifecycleState",
    "PlatformLifecycleTransition",
    "PlatformMaintenanceWindow",
    "PlatformMigration",
    "PlatformMigrationStatus",
    "PlatformUpgrade",
    "PlatformUpgradeStatus",
    "PlatformVersionInfo",
]
