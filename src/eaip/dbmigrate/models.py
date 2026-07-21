"""Data models for database migration — scripts, executions, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ScriptStatus(StrEnum):
    """Lifecycle status of a migration script."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    EXECUTED = "executed"
    ROLLED_BACK = "rolled_back"


class MigrationScript(BaseModel):
    """A single database migration script."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    version: str
    database_type: str
    author: str
    status: ScriptStatus = Field(default=ScriptStatus.DRAFT)
    description: str = Field(default="")
    content: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MigrationExecution(BaseModel):
    """A record of a migration script being executed against an environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    script_id: str
    environment: str
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    output: str = Field(default="")
    error: str = Field(default="")
    success: bool = Field(default=False)


class DBMigrateConfig(BaseModel):
    """Configuration for the database migration assistant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    require_review: bool = Field(default=True)
    backup_before_execution: bool = Field(default=True)
    max_retries: int = Field(default=2, ge=0)
    default_timeout_seconds: int = Field(default=300, ge=1)


__all__ = [
    "DBMigrateConfig",
    "MigrationExecution",
    "MigrationScript",
    "ScriptStatus",
]
