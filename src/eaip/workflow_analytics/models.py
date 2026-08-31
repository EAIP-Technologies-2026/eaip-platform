"""Workflow analytics domain models — metrics, reports, throughput, bottlenecks, trends."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AnalyticsPeriod(StrEnum):
    LAST_HOUR = "last_hour"
    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"
    CUSTOM = "custom"


class WorkflowMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str
    workflow_name: str = ""
    total_executions: int = 0
    succeeded: int = 0
    failed: int = 0
    avg_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    min_duration_seconds: float = 0.0
    p50_duration_seconds: float = 0.0
    p95_duration_seconds: float = 0.0
    p99_duration_seconds: float = 0.0
    period: AnalyticsPeriod = AnalyticsPeriod.LAST_24H
    collected_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThroughputAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str
    period: AnalyticsPeriod
    total_executions: int = 0
    executions_per_hour: float = 0.0
    peak_hour: str = ""
    peak_executions: int = 0
    throughput_trend: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class BottleneckReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str
    bottleneck_type: str = ""
    description: str = ""
    affected_steps: tuple[str, ...] = Field(default_factory=tuple)
    severity: str = "medium"
    avg_wait_time_seconds: float = 0.0
    suggested_action: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class PerformanceTrend(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str
    metric_name: str = ""
    direction: str = "stable"
    change_percent: float = 0.0
    confidence: float = 0.0
    baseline_avg: float = 0.0
    current_avg: float = 0.0
    data_points: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowAnalyticsReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    workflow_id: str
    period: AnalyticsPeriod = AnalyticsPeriod.LAST_24H
    metrics: WorkflowMetrics | None = None
    throughput: ThroughputAnalysis | None = None
    bottlenecks: tuple[BottleneckReport, ...] = Field(default_factory=tuple)
    trends: tuple[PerformanceTrend, ...] = Field(default_factory=tuple)
    sla_compliance_pct: float = 0.0
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowAnalyticsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    collection_interval_seconds: float = 300.0
    retention_days: int = 90
    enable_bottleneck_detection: bool = True
    enable_trend_analysis: bool = True
    enable_sla_tracking: bool = True
    sla_threshold_seconds: float = 3600.0
    max_bottlenecks_per_report: int = 10


__all__ = [
    "AnalyticsPeriod",
    "BottleneckReport",
    "PerformanceTrend",
    "ThroughputAnalysis",
    "WorkflowAnalyticsConfig",
    "WorkflowAnalyticsReport",
    "WorkflowMetrics",
]
