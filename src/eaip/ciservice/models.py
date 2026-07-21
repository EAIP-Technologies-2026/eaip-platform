"""CI domain models — pipelines, builds, artifacts, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class BuildStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Pipeline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    repo_url: str
    branch: str = "main"
    steps: tuple[str, ...] = Field(default=())
    triggers: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class Build(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    pipeline_id: str
    commit_sha: str
    status: BuildStatus = BuildStatus.PENDING
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    logs: str = ""
    artifacts: tuple[str, ...] = Field(default=())


class CIArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    build_id: str
    name: str
    url: str
    size_bytes: int = 0


class CIConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_builds: int = 5
    default_timeout_minutes: int = 30
    log_retention_days: int = 30
    artifact_retention_days: int = 7
    enable_notifications: bool = True


__all__ = [
    "Build",
    "BuildStatus",
    "CIArtifact",
    "CIConfig",
    "Pipeline",
]
