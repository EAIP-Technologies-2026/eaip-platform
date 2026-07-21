"""Data models for the pipeline orchestration engine."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Stage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    pipeline_id: str
    name: str
    order: int = Field(default=0, ge=0)
    depends_on: tuple[str, ...] = Field(default=())
    timeout_seconds: int = Field(default=300, ge=1)
    retry_count: int = Field(default=0, ge=0)
    status: StageStatus = Field(default=StageStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)


class Pipeline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    stages: tuple[Stage, ...] = Field(default=())
    status: str = Field(default="inactive")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineRun(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    pipeline_id: str
    status: str = Field(default="pending")
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    error_message: str = Field(default="")
    stages: tuple[Stage, ...] = Field(default=())


class OrchestratorConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_stages: int = Field(default=5, ge=1)
    default_timeout_seconds: int = Field(default=300, ge=1)
    max_retries: int = Field(default=3, ge=0)
    enable_parallel_execution: bool = Field(default=True)


__all__ = [
    "OrchestratorConfig",
    "Pipeline",
    "PipelineRun",
    "Stage",
    "StageStatus",
]
