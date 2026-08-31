"""AI Analytics domain models — metrics, usage, cost, latency, dashboards, and insights."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AiAnalyticsMetricType(StrEnum):
    TOKENS = "tokens"
    REQUESTS = "requests"
    LATENCY = "latency"
    ERRORS = "errors"
    COST = "cost"
    CUSTOM = "custom"


class AiAnalyticsReportPeriod(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AiAnalyticsInsightSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AiAnalyticsConfig(BaseModel):
    """Configuration for the AI analytics subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    export_enabled: bool = True
    anomaly_detection_enabled: bool = True
    trend_detection_enabled: bool = True
    forecast_enabled: bool = True
    retention_days: int = 90
    export_interval_minutes: float = 60.0
    anomaly_sensitivity: float = 2.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiAnalyticsMetric(BaseModel):
    """A single AI analytics metric data point."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: AiAnalyticsMetricType = AiAnalyticsMetricType.CUSTOM
    name: str
    value: float = 0.0
    unit: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    tags: dict[str, str] = Field(default_factory=dict)
    source: str = ""
    labels: dict[str, str] = Field(default_factory=dict)


class AiModelUsageMetrics(BaseModel):
    """AI model usage metrics — request volume and concurrency."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = ""
    deployment_id: str = ""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_concurrent_requests: int = 0
    peak_concurrent_requests: int = 0
    timestamp: datetime = Field(default_factory=utc_now)


class AiTokenUsageMetrics(BaseModel):
    """AI token usage metrics — input, output, and total token counts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = ""
    deployment_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    timestamp: datetime = Field(default_factory=utc_now)


class AiLatencyMetrics(BaseModel):
    """AI latency metrics — response times for model invocations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = ""
    deployment_id: str = ""
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=utc_now)


class AiErrorMetrics(BaseModel):
    """AI error metrics — error rates and counts by category."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = ""
    deployment_id: str = ""
    total_errors: int = 0
    error_rate: float = 0.0
    timeout_errors: int = 0
    rate_limit_errors: int = 0
    auth_errors: int = 0
    content_filter_errors: int = 0
    server_errors: int = 0
    other_errors: int = 0
    timestamp: datetime = Field(default_factory=utc_now)


class AiCostMetrics(BaseModel):
    """AI cost metrics — monetary cost breakdown by model and deployment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = ""
    deployment_id: str = ""
    cost_per_request: float = 0.0
    cost_per_token: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"
    estimated_monthly_cost: float = 0.0
    timestamp: datetime = Field(default_factory=utc_now)


class AiAnalyticsReport(BaseModel):
    """A comprehensive AI analytics report covering multiple metrics and dimensions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    period: AiAnalyticsReportPeriod = AiAnalyticsReportPeriod.DAILY
    time_range: tuple[datetime, datetime]
    model_ids: tuple[str, ...] = Field(default_factory=tuple)
    deployment_ids: tuple[str, ...] = Field(default_factory=tuple)
    usage_metrics: dict[str, AiModelUsageMetrics] = Field(default_factory=dict)
    token_metrics: dict[str, AiTokenUsageMetrics] = Field(default_factory=dict)
    latency_metrics: dict[str, AiLatencyMetrics] = Field(default_factory=dict)
    error_metrics: dict[str, AiErrorMetrics] = Field(default_factory=dict)
    cost_metrics: dict[str, AiCostMetrics] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiAnalyticsDashboardWidget(BaseModel):
    """A single widget on an AI analytics dashboard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str = ""
    widget_type: str = "timeseries"
    metric_types: tuple[AiAnalyticsMetricType, ...] = Field(default_factory=tuple)
    model_ids: tuple[str, ...] = Field(default_factory=tuple)
    width: int = 1
    height: int = 1
    config: dict[str, Any] = Field(default_factory=dict)


class AiAnalyticsDashboard(BaseModel):
    """AI analytics dashboard composed of multiple widgets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    widgets: tuple[AiAnalyticsDashboardWidget, ...] = Field(default_factory=tuple)
    refresh_interval_seconds: float = 60.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiAnomalyDetectionResult(BaseModel):
    """Result of an anomaly detection on AI analytics data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    metric_id: str
    model_id: str = ""
    deployment_id: str = ""
    value: float = 0.0
    expected_value: float = 0.0
    deviation: float = 0.0
    severity: AiAnalyticsInsightSeverity = AiAnalyticsInsightSeverity.WARNING
    detected_at: datetime = Field(default_factory=utc_now)
    tags: dict[str, str] = Field(default_factory=dict)


class AiAnalyticsTrend(BaseModel):
    """Trend direction and magnitude for an AI analytics metric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    model_id: str = ""
    deployment_id: str = ""
    direction: str = "stable"
    change_percent: float = 0.0
    confidence: float = 0.0
    period_comparison: dict[str, float] = Field(default_factory=dict)
    computed_at: datetime = Field(default_factory=utc_now)


class AiAnalyticsForecast(BaseModel):
    """Forecasted values for an AI analytics metric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    metric_id: str
    model_id: str = ""
    deployment_id: str = ""
    forecast_points: tuple[tuple[datetime, float], ...] = Field(default_factory=tuple)
    confidence_upper: tuple[float, ...] = Field(default_factory=tuple)
    confidence_lower: tuple[float, ...] = Field(default_factory=tuple)
    horizon_hours: float = 24.0
    generated_at: datetime = Field(default_factory=utc_now)


class AiAnalyticsInsight(BaseModel):
    """An actionable insight derived from AI analytics data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    description: str = ""
    severity: AiAnalyticsInsightSeverity = AiAnalyticsInsightSeverity.INFO
    metric_ids: tuple[str, ...] = Field(default_factory=tuple)
    model_ids: tuple[str, ...] = Field(default_factory=tuple)
    recommendation: str = ""
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiAnalyticsExport(BaseModel):
    """An export of AI analytics data to an external destination."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    report_id: str = ""
    format: str = "json"
    destination: str = ""
    exported_at: datetime = Field(default_factory=utc_now)
    record_count: int = 0
    success: bool = True
    error_message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AiAnalyticsConfig",
    "AiAnalyticsDashboard",
    "AiAnalyticsDashboardWidget",
    "AiAnalyticsExport",
    "AiAnalyticsForecast",
    "AiAnalyticsInsight",
    "AiAnalyticsInsightSeverity",
    "AiAnalyticsMetric",
    "AiAnalyticsMetricType",
    "AiAnalyticsReport",
    "AiAnalyticsReportPeriod",
    "AiAnalyticsTrend",
    "AiAnomalyDetectionResult",
    "AiCostMetrics",
    "AiErrorMetrics",
    "AiLatencyMetrics",
    "AiModelUsageMetrics",
    "AiTokenUsageMetrics",
]
