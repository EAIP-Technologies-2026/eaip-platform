"""Pydantic models for model fallback chains, strategies, and graceful degradation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class FallbackStrategy(StrEnum):
    """Ordering strategy for fallback steps."""

    SEQUENTIAL = "sequential"
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"
    LATENCY_BASED = "latency_based"
    WEIGHTED = "weighted"
    CONCURRENT = "concurrent"


class FallbackStepStatus(StrEnum):
    """Status of an individual fallback step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


class FallbackExecutionStatus(StrEnum):
    """Overall status of a fallback chain execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEGRADED = "degraded"
    TIMED_OUT = "timed_out"


class DegradationLevel(StrEnum):
    """Level of graceful degradation."""

    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class FallbackHealthStatus(StrEnum):
    """Health status of a fallback target."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FallbackCondition(BaseModel):
    """Condition that determines when a fallback step should be attempted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_latency_ms: float | None = Field(
        default=None, ge=0, description="Maximum acceptable latency in ms"
    )
    max_errors: int | None = Field(
        default=None, ge=0, description="Maximum consecutive errors before fallback"
    )
    error_rate_threshold: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Error rate threshold (0.0-1.0)"
    )
    min_confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Minimum confidence score (0.0-1.0)"
    )
    custom_evaluator: str | None = Field(default=None, description="Custom evaluator function name")


class FallbackTrigger(BaseModel):
    """Defines what triggers a fallback to the next step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    on_error_types: tuple[str, ...] = Field(
        default=(), description="Exception types that trigger fallback"
    )
    on_timeout: bool = Field(default=True, description="Trigger fallback on timeout")
    on_latency_exceeded: bool = Field(
        default=False, description="Trigger fallback when latency exceeds threshold"
    )
    on_error_rate_exceeded: bool = Field(
        default=False, description="Trigger fallback when error rate exceeds threshold"
    )
    on_confidence_low: bool = Field(
        default=False, description="Trigger fallback when confidence is low"
    )
    on_degraded_health: bool = Field(
        default=True, description="Trigger fallback when target health is degraded"
    )


class FallbackStep(BaseModel):
    """A single step in a model fallback chain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Name of the fallback step")
    model_id: str = Field(description="Model identifier to use for this step")
    priority: int = Field(default=0, ge=0, description="Priority (lower = tried first)")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Weight for weighted strategies")
    condition: FallbackCondition | None = Field(
        default=None, description="Condition for attempting this step"
    )
    timeout_ms: float | None = Field(default=None, ge=0, description="Per-step timeout in ms")
    max_retries: int = Field(default=0, ge=0, description="Max retries for this step")


class FallbackPolicy(BaseModel):
    """Policy governing fallback behavior."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: FallbackStrategy = Field(
        default=FallbackStrategy.SEQUENTIAL, description="Fallback ordering strategy"
    )
    max_steps: int = Field(default=3, ge=1, le=10, description="Maximum steps to attempt")
    global_timeout_ms: float | None = Field(
        default=None, ge=0, description="Global timeout for the entire chain"
    )
    stop_on_first_success: bool = Field(
        default=True, description="Stop chain after first successful step"
    )
    degrade_gracefully: bool = Field(
        default=True, description="Degrade rather than fail when all steps exhausted"
    )


class ModelFallbackChain(BaseModel):
    """A named fallback chain composed of ordered steps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chain_id: str = Field(description="Unique identifier for this chain")
    name: str = Field(description="Human-readable chain name")
    steps: tuple[FallbackStep, ...] = Field(description="Ordered fallback steps")
    policy: FallbackPolicy = Field(default_factory=FallbackPolicy, description="Fallback policy")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class FallbackConfig(BaseModel):
    """Top-level configuration for model fallback."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chains: tuple[ModelFallbackChain, ...] = Field(
        default=(), description="Registered fallback chains"
    )
    default_policy: FallbackPolicy = Field(
        default_factory=FallbackPolicy, description="Default policy for new chains"
    )
    degradation: GracefulDegradationConfig | None = Field(
        default=None, description="Graceful degradation config"
    )
    history_ttl_days: int = Field(default=30, ge=1, description="Days to retain fallback history")
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")


class FallbackExecution(BaseModel):
    """Record of a single fallback chain execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    execution_id: str = Field(description="Unique execution identifier")
    chain_id: str = Field(description="Chain that was executed")
    status: FallbackExecutionStatus = Field(default=FallbackExecutionStatus.PENDING)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    total_duration_ms: float | None = Field(default=None, ge=0)
    steps_attempted: int = Field(default=0, ge=0)
    steps_succeeded: int = Field(default=0, ge=0)
    steps_failed: int = Field(default=0, ge=0)
    final_model_id: str | None = Field(
        default=None, description="Model used for the final response"
    )
    degradation_level: DegradationLevel = Field(default=DegradationLevel.NONE)
    error: str | None = Field(default=None)


class FallbackResult(BaseModel):
    """Result returned from a fallback chain execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    success: bool = Field(description="Whether the chain produced a successful result")
    output: Any | None = Field(default=None, description="Final model output")
    model_id: str | None = Field(default=None, description="Model that produced the output")
    execution_id: str = Field(description="Associated execution record ID")
    duration_ms: float = Field(default=0.0, ge=0, description="Total duration in ms")
    degradation_level: DegradationLevel = Field(default=DegradationLevel.NONE)
    error: str | None = Field(default=None)


class FallbackMetrics(BaseModel):
    """Collected metrics for a fallback chain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chain_id: str = Field(description="Chain these metrics belong to")
    total_executions: int = Field(default=0, ge=0)
    successful_executions: int = Field(default=0, ge=0)
    failed_executions: int = Field(default=0, ge=0)
    degraded_executions: int = Field(default=0, ge=0)
    avg_duration_ms: float = Field(default=0.0, ge=0)
    p95_duration_ms: float = Field(default=0.0, ge=0)
    p99_duration_ms: float = Field(default=0.0, ge=0)
    last_execution_at: datetime | None = Field(default=None)
    collected_at: datetime = Field(default_factory=utc_now)


class FallbackHistoryEntry(BaseModel):
    """A single history entry for a fallback event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entry_id: str = Field(description="Unique entry identifier")
    execution_id: str = Field(description="Associated execution ID")
    chain_id: str = Field(description="Chain identifier")
    event_type: str = Field(description="Type of history event")
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class GracefulDegradationConfig(BaseModel):
    """Configuration for graceful degradation behavior."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, description="Enable graceful degradation")
    max_degradation_level: DegradationLevel = Field(
        default=DegradationLevel.CRITICAL, description="Maximum allowed degradation"
    )
    fallback_to_static: bool = Field(
        default=False, description="Fallback to static response when all degraded"
    )
    static_response: str | None = Field(
        default=None, description="Static response when fully degraded"
    )
    notify_on_degradation: bool = Field(
        default=True, description="Emit event on degradation level change"
    )
    cooldown_seconds: float = Field(
        default=30.0, ge=0, description="Cooldown between degradation level checks"
    )


__all__ = [
    "DegradationLevel",
    "FallbackCondition",
    "FallbackConfig",
    "FallbackExecution",
    "FallbackExecutionStatus",
    "FallbackHealthStatus",
    "FallbackHistoryEntry",
    "FallbackMetrics",
    "FallbackPolicy",
    "FallbackResult",
    "FallbackStep",
    "FallbackStepStatus",
    "FallbackStrategy",
    "FallbackTrigger",
    "GracefulDegradationConfig",
    "ModelFallbackChain",
]
