"""Domain models for platform operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class MaintenanceWindow(BaseModel):
    """A scheduled maintenance window."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    status: str = "scheduled"
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    components: tuple[str, ...] = Field(default=())
    reason: str = ""
    created_by: str = "system"
    metadata: dict[str, str] = Field(default_factory=dict)
    notify_users: tuple[str, ...] = Field(default=())


class BackupComponent(BaseModel):
    """A single component within a backup manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str = "config"
    status: str = "pending"
    size_bytes: int = 0
    record_count: int = 0
    checksum: str = ""
    error: str = ""


class BackupManifest(BaseModel):
    """A manifest describing a system backup."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    components: tuple[BackupComponent, ...] = Field(default=())
    status: str = "in_progress"
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    size_bytes: int = 0
    checksum: str = ""
    location: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    retention_days: int = 30


class MigrationStep(BaseModel):
    """A single step within a migration plan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    description: str = ""
    type: str = "data"
    status: str = "pending"
    duration_ms: float = 0.0
    error: str = ""
    rollback_step_id: str = ""


class MigrationPlan(BaseModel):
    """A migration plan describing a version upgrade."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_version: str
    target_version: str
    steps: tuple[MigrationStep, ...] = Field(default=())
    status: str = "draft"
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    rollback_plan: str = ""


class SystemHealthSnapshot(BaseModel):
    """A point-in-time snapshot of system health."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    timestamp: datetime = Field(default_factory=utc_now)
    overall_status: str = "unknown"
    component_statuses: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    active_alerts: tuple[str, ...] = Field(default=())
    version_info: dict[str, str] = Field(default_factory=dict)
    uptime_seconds: float = 0.0


class OperationsConfig(BaseModel):
    """Configuration settings for the operations subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    backup_retention_days: int = 30
    auto_backup_enabled: bool = False
    auto_backup_interval_hours: int = 24
    maintenance_approval_required: bool = True
    health_check_interval_seconds: int = 60
    max_backup_size_bytes: int = 10_737_418_240


__all__ = [
    "BackupComponent",
    "BackupManifest",
    "MaintenanceWindow",
    "MigrationPlan",
    "MigrationStep",
    "OperationsConfig",
    "SystemHealthSnapshot",
]
