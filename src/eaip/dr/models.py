"""DR domain models — plans, components, steps, test results, failover events, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PlanPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    TESTED = "tested"
    FAILED = "failed"
    ARCHIVED = "archived"


class ComponentType(StrEnum):
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    CONFIG = "config"
    SECURITY = "security"
    DNS = "dns"


class StepType(StrEnum):
    VERIFY = "verify"
    BACKUP = "backup"
    FAILOVER = "failover"
    RESTORE = "restore"
    TEST = "test"
    NOTIFY = "notify"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DrTestResultStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


class FailoverEventStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DrComponent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: ComponentType
    criticality: PlanPriority = PlanPriority.MEDIUM
    backup_source: str = ""
    recovery_procedure: str = ""
    max_allowed_downtime_seconds: int = 300
    metadata: dict[str, Any] = Field(default_factory=dict)


class DrStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    plan_id: str
    name: str
    description: str = ""
    order: int = 0
    type: StepType = StepType.VERIFY
    automation_ref: str = ""
    timeout_seconds: int = 60
    required_steps: tuple[str, ...] = Field(default=())
    status: StepStatus = StepStatus.PENDING
    duration_ms: float = 0.0
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DrPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    priority: PlanPriority = PlanPriority.MEDIUM
    status: PlanStatus = PlanStatus.DRAFT
    rto_seconds: int = 3600
    rpo_seconds: int = 900
    components: tuple[DrComponent, ...] = Field(default=())
    steps: tuple[DrStep, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_tested_at: datetime | None = None
    test_results: tuple[DrTestResult, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class DrTestResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    plan_id: str
    status: DrTestResultStatus = DrTestResultStatus.PASSED
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    rto_achieved_seconds: float | None = None
    rpo_achieved_seconds: float | None = None
    steps_passed: int = 0
    steps_failed: int = 0
    steps_total: int = 0
    findings: tuple[str, ...] = Field(default=())
    recommendations: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class FailoverEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    plan_id: str
    triggered_by: str = ""
    reason: str = ""
    status: FailoverEventStatus = FailoverEventStatus.PENDING
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    components_affected: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class DrConfig(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    auto_failover_enabled: bool = False
    health_check_interval_seconds: int = 30
    max_retries: int = 3
    notify_on_failover: bool = True
    failover_timeout_seconds: int = 600
    test_interval_days: int = 30


__all__ = [
    "ComponentType",
    "DrComponent",
    "DrConfig",
    "DrPlan",
    "DrStep",
    "DrTestResult",
    "DrTestResultStatus",
    "FailoverEvent",
    "FailoverEventStatus",
    "PlanPriority",
    "PlanStatus",
    "StepStatus",
    "StepType",
]
