"""Execution history domain models — records, events, queries, filters, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class ExecutionEventType(StrEnum):
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    LOG = "log"


class ExecutionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    trigger: str = ""
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    run_by: str = ""
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    execution_id: str
    event_type: ExecutionEventType
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class ExecutionSpan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    execution_id: str
    parent_span_id: str | None = None
    span_id: str = ""
    status: ExecutionStatus = ExecutionStatus.RUNNING
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    duration_ms: float | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionFilter(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_ids: tuple[str, ...] = Field(default=())
    statuses: tuple[ExecutionStatus, ...] = Field(default=())
    run_by: str = ""
    trigger: str = ""
    date_from: datetime | None = None
    date_to: datetime | None = None
    tags: tuple[str, ...] = Field(default=())
    search: str = ""


class ExecutionHistoryQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    filter: ExecutionFilter = Field(default_factory=ExecutionFilter)
    offset: int = 0
    limit: int = 50
    sort_by: str = "created_at"
    sort_desc: bool = True


class ExecutionHistoryResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    records: tuple[ExecutionRecord, ...] = Field(default=())
    total: int = 0
    offset: int = 0
    limit: int = 50
    has_more: bool = False


class ExecutionHistoryStats(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_executions: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    pending: int = 0
    cancelled: int = 0
    skipped: int = 0
    avg_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0


class ExecutionHistoryConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    retention_days: int = 90
    max_records_per_workflow: int = 10_000
    archive_enabled: bool = False
    export_max_records: int = 1_000
    enable_analytics: bool = True
    compaction_enabled: bool = False
    compaction_interval_hours: int = 24


__all__ = [
    "ExecutionEvent",
    "ExecutionEventType",
    "ExecutionFilter",
    "ExecutionHistoryConfig",
    "ExecutionHistoryQuery",
    "ExecutionHistoryResult",
    "ExecutionHistoryStats",
    "ExecutionRecord",
    "ExecutionSpan",
    "ExecutionStatus",
]
