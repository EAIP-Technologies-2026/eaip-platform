"""Pydantic models for the agent performance analyzer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ExecutionRecord(BaseModel):
    """Record of a single agent execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this execution")
    agent_id: str = Field(description="ID of the agent that executed")
    task_type: str = Field(description="Type of task executed")
    duration_ms: float = Field(
        default=0.0, ge=0.0, description="Execution duration in milliseconds"
    )
    tokens_used: int = Field(default=0, ge=0, description="Number of tokens consumed")
    success: bool = Field(default=True, description="Whether the execution succeeded")
    timestamp: datetime = Field(default_factory=utc_now, description="When the execution occurred")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )


class PerformanceMetrics(BaseModel):
    """Aggregated performance metrics for an agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_id: str = Field(description="ID of the agent")
    total_executions: int = Field(default=0, ge=0, description="Total number of executions")
    successful_executions: int = Field(
        default=0, ge=0, description="Number of successful executions"
    )
    failed_executions: int = Field(default=0, ge=0, description="Number of failed executions")
    avg_duration_ms: float = Field(default=0.0, ge=0.0, description="Average execution duration")
    p95_duration_ms: float = Field(default=0.0, ge=0.0, description="P95 execution duration")
    total_tokens_used: int = Field(default=0, ge=0, description="Total tokens consumed")
    avg_tokens_per_execution: float = Field(
        default=0.0, ge=0.0, description="Average tokens per execution"
    )
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Success rate (0.0-1.0)")
    period_start: datetime = Field(description="Start of the measurement period")
    period_end: datetime = Field(description="End of the measurement period")


class BottleneckReport(BaseModel):
    """Report identifying a performance bottleneck."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this bottleneck report")
    agent_id: str = Field(description="ID of the affected agent")
    metric: str = Field(
        description="The metric that triggered the bottleneck (e.g. duration_ms, tokens)"
    )
    threshold: float = Field(description="The threshold that was exceeded")
    actual_value: float = Field(description="The actual value observed")
    recommendation: str = Field(description="Recommended action to address the bottleneck")
    detected_at: datetime = Field(
        default_factory=utc_now, description="When the bottleneck was detected"
    )


class AnalyzerConfig(BaseModel):
    """Configuration for the agent performance analyzer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    duration_threshold_ms: float = Field(
        default=5000.0, ge=0.0, description="Threshold for slow execution warning"
    )
    token_threshold: int = Field(
        default=4096, ge=0, description="Threshold for high token usage warning"
    )
    bottleneck_window_minutes: int = Field(
        default=60, ge=1, description="Window for bottleneck detection"
    )
    history_retention_days: int = Field(
        default=90, ge=1, description="Days to retain execution history"
    )


__all__ = [
    "AnalyzerConfig",
    "BottleneckReport",
    "ExecutionRecord",
    "PerformanceMetrics",
]
