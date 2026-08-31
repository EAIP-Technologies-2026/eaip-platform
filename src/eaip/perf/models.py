"""Performance management data models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class MetricType(StrEnum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    CPU = "cpu"
    IO = "io"


class BenchmarkRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RegressionDirection(StrEnum):
    IMPROVEMENT = "improvement"
    REGRESSION = "regression"
    UNCHANGED = "unchanged"


class RegressionSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegressionStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class BenchmarkDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    component: str
    metric_type: MetricType
    target_value: float
    threshold_value: float = Field(default=0.0)
    unit: str = Field(default="")
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    benchmark_id: str
    status: BenchmarkRunStatus = Field(default=BenchmarkRunStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0)
    result_value: float = Field(default=0.0)
    passed: bool = Field(default=False)
    error: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class LoadTestScenario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    target_component: str
    concurrency_level: int = Field(default=1, ge=1)
    duration_seconds: int = Field(default=30, ge=1)
    ramp_up_seconds: int = Field(default=0, ge=0)
    endpoint_pattern: str = Field(default="")
    request_config: dict[str, Any] = Field(default_factory=dict)
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)


class LoadTestResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    scenario_id: str
    status: BenchmarkRunStatus = Field(default=BenchmarkRunStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0)
    total_requests: int = Field(default=0, ge=0)
    successful_requests: int = Field(default=0, ge=0)
    failed_requests: int = Field(default=0, ge=0)
    avg_response_time_ms: float = Field(default=0.0, ge=0.0)
    p50_response_time: float = Field(default=0.0, ge=0.0)
    p95_response_time: float = Field(default=0.0, ge=0.0)
    p99_response_time: float = Field(default=0.0, ge=0.0)
    throughput_reqs_per_sec: float = Field(default=0.0, ge=0.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PerformanceRegression(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    benchmark_id: str
    baseline_run_id: str
    current_run_id: str
    metric_type: MetricType
    baseline_value: float = Field(default=0.0)
    current_value: float = Field(default=0.0)
    change_percent: float = Field(default=0.0)
    direction: RegressionDirection = Field(default=RegressionDirection.UNCHANGED)
    severity: RegressionSeverity = Field(default=RegressionSeverity.LOW)
    detected_at: datetime = Field(default_factory=utc_now)
    status: RegressionStatus = Field(default=RegressionStatus.OPEN)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PerfConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    benchmark_interval_hours: int = Field(default=24, ge=1)
    regression_threshold_percent: float = Field(default=10.0, ge=0.0)
    max_concurrent_runs: int = Field(default=5, ge=1)
    history_retention_days: int = Field(default=90, ge=1)
    enable_auto_benchmark: bool = Field(default=True)
