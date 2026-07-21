"""Data migration domain models — migrations, steps, batches, transforms, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MigrationType(StrEnum):
    SCHEMA = "schema"
    DATA = "data"
    CONFIG = "config"
    PLUGIN = "plugin"


class MigrationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class StepDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    VERIFY = "verify"
    ROLLBACK = "rollback"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BatchStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Migration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    version: str
    description: str
    type: MigrationType
    status: MigrationStatus = Field(default=MigrationStatus.PENDING)
    checksum: str = Field(default="")
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0)
    error: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MigrationStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    migration_id: str
    order: int
    description: str
    type: StepDirection
    status: StepStatus = Field(default=StepStatus.PENDING)
    duration_ms: float = Field(default=0.0)
    error: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MigrationBatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    migrations: tuple[str, ...] = Field(default=())
    status: BatchStatus = Field(default=BatchStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataTransform(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_type: str
    target_type: str
    mapping_rules: dict[str, Any] = Field(default_factory=dict)
    validation_rules: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MigrationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_auto_migrate: bool = Field(default=True)
    backup_before_migrate: bool = Field(default=True)
    max_retries: int = Field(default=3)
    timeout_seconds: int = Field(default=300)
    enable_validation: bool = Field(default=True)
    history_retention_days: int = Field(default=90)
    concurrent_migrations: int = Field(default=1)
