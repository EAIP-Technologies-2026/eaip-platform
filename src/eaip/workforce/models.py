"""Workforce models — WorkerDefinition, WorkerAssignment, WorkforceConfig, WorkforceMetrics."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AssignmentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkerType(StrEnum):
    AGENT = "agent"
    WORKFLOW = "workflow"
    JOB = "job"


class WorkerDefinition(BaseModel):
    """Definition of a single worker in the workforce."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    worker_type: WorkerType
    agent_id: str = ""
    workflow_id: str = ""
    job_id: str = ""
    description: str = ""
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    max_concurrent_runs: int = 1
    timeout_seconds: float = 0.0


class WorkerAssignment(BaseModel):
    """A task assigned to a worker for execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    worker_id: str
    task_description: str
    status: AssignmentStatus = AssignmentStatus.PENDING
    assigned_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    result: str = ""
    error: str | None = None
    run_id: str = ""
    priority: int = 0


class WorkforceConfig(BaseModel):
    """Configuration for the workforce runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_workers: int = 10
    default_timeout_seconds: float = 300.0
    enable_auto_scaling: bool = False
    health_check_interval_seconds: float = 60.0


class WorkforceMetrics(BaseModel):
    """Snapshot of workforce performance metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_assignments: int = 0
    active_assignments: int = 0
    completed_assignments: int = 0
    failed_assignments: int = 0
    avg_duration_ms: float = 0.0
    workers_registered: int = 0


__all__ = [
    "AssignmentStatus",
    "WorkerAssignment",
    "WorkerDefinition",
    "WorkerType",
    "WorkforceConfig",
    "WorkforceMetrics",
]
