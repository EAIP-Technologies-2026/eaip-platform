"""Quality & Testing data models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TestCaseType(StrEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    REGRESSION = "regression"
    PERFORMANCE = "performance"


class TestCaseStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class TestExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class QualityGateStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MetricOperator(StrEnum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"


class RegressionStatus(StrEnum):
    CLEAN = "clean"
    REGRESSION = "regression"
    IMPROVED = "improved"


class MetricType(StrEnum):
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    CPU = "cpu"


class TestCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    type: TestCaseType = Field(default=TestCaseType.UNIT)
    status: TestCaseStatus = Field(default=TestCaseStatus.DRAFT)
    component: str = Field(default="")
    input_data: dict[str, Any] = Field(default_factory=dict)
    expected_output: dict[str, Any] = Field(default_factory=dict)
    assertions: tuple[str, ...] = Field(default=())
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    author: str = Field(default="")
    priority: Priority = Field(default=Priority.MEDIUM)


class TestSuite(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    test_ids: tuple[str, ...] = Field(default=())
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    parallel_execution: bool = Field(default=False)
    timeout_seconds: int = Field(default=300)
    created_at: datetime = Field(default_factory=utc_now)


class TestExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    test_id: str
    suite_id: str = Field(default="")
    status: TestExecutionStatus = Field(default=TestExecutionStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0)
    result: dict[str, Any] = Field(default_factory=dict)
    error: str = Field(default="")
    assertion_results: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityCondition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metric: str
    operator: MetricOperator
    value: float
    description: str = Field(default="")


class QualityGate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    conditions: tuple[QualityCondition, ...] = Field(default=())
    status: QualityGateStatus = Field(default=QualityGateStatus.PENDING)
    evaluated_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CoverageReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    component: str
    line_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    branch_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    function_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    uncovered_lines: tuple[int, ...] = Field(default=())
    total_lines: int = Field(default=0, ge=0)
    covered_lines: int = Field(default=0, ge=0)
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegressionChange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    test_id: str
    test_name: str
    baseline_status: str
    current_status: str
    baseline_duration_ms: float = Field(default=0.0)
    current_duration_ms: float = Field(default=0.0)
    delta_ms: float = Field(default=0.0)


class RegressionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    baseline_id: str
    current_id: str
    component: str
    status: RegressionStatus = Field(default=RegressionStatus.CLEAN)
    changes: tuple[RegressionChange, ...] = Field(default=())
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PerformanceBenchmark(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    component: str
    metric: MetricType
    value: float
    unit: str = Field(default="")
    threshold: float = Field(default=0.0)
    status: QualityGateStatus = Field(default=QualityGateStatus.PASS)
    measured_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_timeout_seconds: int = Field(default=300)
    max_retries: int = Field(default=3)
    enable_parallel_execution: bool = Field(default=False)
    coverage_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    enable_regression_detection: bool = Field(default=True)
    history_retention_days: int = Field(default=90)
