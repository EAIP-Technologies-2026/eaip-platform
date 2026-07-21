from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SourceType(StrEnum):
    HTTP = "http"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"
    QUEUE = "queue"


class SinkType(StrEnum):
    HTTP = "http"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"
    QUEUE = "queue"


class StepType(StrEnum):
    TRANSFORM = "transform"
    FILTER = "filter"
    VALIDATE = "validate"
    ENRICH = "enrich"
    AGGREGATE = "aggregate"
    SCRIPT = "script"


class ErrorHandlingMode(StrEnum):
    ABORT = "abort"
    SKIP = "skip"
    ISOLATION = "isolation"


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"


class DataSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: SourceType
    config: dict[str, Any] = Field(default_factory=dict)
    credentials_ref: str | None = None
    data_schema: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = 3
    timeout_seconds: float = 30.0


class DataSink(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: SinkType
    config: dict[str, Any] = Field(default_factory=dict)
    credentials_ref: str | None = None
    data_schema: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: StepType
    config: dict[str, Any] = Field(default_factory=dict)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class Pipeline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    source_id: str
    sink_id: str
    steps: tuple[PipelineStep, ...] = Field(default_factory=tuple)
    schedule_cron: str | None = None
    enabled: bool = True
    max_concurrent: int = 1
    error_handling: ErrorHandlingMode = ErrorHandlingMode.ABORT
    timeout_seconds: float = 300.0
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    pipeline_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    records_read: int = 0
    records_written: int = 0
    records_failed: int = 0
    error: str | None = None
    step_results: dict[str, Any] = Field(default_factory=dict)
    trigger_type: TriggerType = TriggerType.MANUAL


class DataRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    schema_version: str = ""
    checksum: str = ""


class PipelineConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_records_per_run: int = 10000
    default_batch_size: int = 100
    enable_lineage_tracking: bool = True
    retention_days: int = 30
    max_execution_history: int = 1000


__all__ = [
    "DataRecord",
    "DataSink",
    "DataSource",
    "ErrorHandlingMode",
    "ExecutionStatus",
    "Pipeline",
    "PipelineConfig",
    "PipelineExecution",
    "PipelineStep",
    "SinkType",
    "SourceType",
    "StepType",
    "TriggerType",
]
