"""Retry orchestration domain models - config, policy, strategy, state, execution, metrics."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class BackoffStrategy(StrEnum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    JITTER = "jitter"
    DECORRELATED_JITTER = "decorrelated_jitter"


class RetryStrategy(StrEnum):
    SIMPLE = "simple"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    JITTER_BACKOFF = "jitter_backoff"
    DECORRELATED_JITTER_BACKOFF = "decorrelated_jitter_backoff"
    CUSTOM = "custom"


class RetryStateStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXHAUSTED = "exhausted"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class RetryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    jitter: float = 0.1
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_exceptions: tuple[str, ...] = Field(default_factory=tuple)
    non_retryable_exceptions: tuple[str, ...] = Field(default_factory=tuple)
    timeout_seconds: float = 0.0
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CircuitBreakerConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_threshold: int = 5
    success_threshold: int = 2
    open_timeout_seconds: float = 30.0
    half_open_max_attempts: int = 3
    consecutive_failure_count: int = 0
    consecutive_success_count: int = 0


class CircuitBreakerState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    state: str = "closed"
    failure_count: int = 0
    success_count: int = 0
    last_failure_at: datetime | None = None
    last_success_at: datetime | None = None
    opened_at: datetime | None = None
    half_opened_at: datetime | None = None
    config: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetryState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    execution_id: str
    attempt: int = 0
    status: RetryStateStatus = RetryStateStatus.PENDING
    next_attempt_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: str = ""
    delay_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetryExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    policy_id: str
    target: str
    attempt: int = 0
    max_attempts: int = 3
    status: RetryStateStatus = RetryStateStatus.PENDING
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    last_error: str = ""
    result: str = ""
    attempts: tuple[RetryState, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetryResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: str
    policy_id: str
    target: str
    success: bool = False
    attempt: int = 0
    total_attempts: int = 0
    result: str = ""
    error: str = ""
    duration_ms: float = 0.0
    exhausted: bool = False
    circuit_broken: bool = False


class RetryOrchestrationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_concurrent_executions: int = 10
    default_max_attempts: int = 3
    default_delay_seconds: float = 1.0
    default_backoff_multiplier: float = 2.0
    default_max_delay_seconds: float = 60.0
    default_jitter: float = 0.1
    default_timeout_seconds: float = 0.0
    enable_circuit_breaker: bool = True
    enable_metrics: bool = True
    metrics_collection_interval_seconds: float = 60.0


class RetryMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    exhausted_count: int = 0
    circuit_breaker_trips: int = 0
    circuit_breaker_resets: int = 0
    avg_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    collected_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "BackoffStrategy",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "RetryExecution",
    "RetryMetrics",
    "RetryOrchestrationConfig",
    "RetryPolicy",
    "RetryResult",
    "RetryState",
    "RetryStateStatus",
    "RetryStrategy",
]
