"""Search analytics domain models — config, logs, metrics, reports, trends, dashboards, funnels."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SearchMetricsPeriod(StrEnum):
    LAST_HOUR = "last_hour"
    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"
    CUSTOM = "custom"


class SearchTrendPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SearchSessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    TIMEOUT = "timeout"


class SearchAnalyticsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    logging_enabled: bool = True
    metrics_collection_interval_seconds: float = 60.0
    retention_days: int = 90
    enable_trend_analysis: bool = True
    enable_alerting: bool = True
    enable_funnel_analysis: bool = True
    enable_abandonment_analysis: bool = True
    popular_query_threshold: int = 10
    zero_result_alert_threshold: int = 5
    max_reports_per_dashboard: int = 20


class SearchQueryLog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    query: str
    timestamp: datetime = Field(default_factory=utc_now)
    user_id: str = ""
    session_id: str = ""
    result_count: int = 0
    duration_ms: float = 0.0
    source: str = ""
    filters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_queries: int = 0
    unique_users: int = 0
    avg_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    total_results_retrieved: int = 0
    zero_result_queries: int = 0
    click_through_rate: float = 0.0
    abandonment_rate: float = 0.0
    period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    collected_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchPerformanceReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    metrics: SearchMetrics | None = None
    avg_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    throughput_per_minute: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchTrend(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_name: str
    period: SearchTrendPeriod = SearchTrendPeriod.DAILY
    direction: str = "stable"
    change_percent: float = 0.0
    confidence: float = 0.0
    baseline_avg: float = 0.0
    current_avg: float = 0.0
    data_points: int = 0
    seasonality_detected: bool = False
    anomaly_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchAnalyticsReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str = ""
    period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    metrics: SearchMetrics | None = None
    performance: SearchPerformanceReport | None = None
    trends: tuple[SearchTrend, ...] = Field(default_factory=tuple)
    popular_queries: tuple[SearchPopularQuery, ...] = Field(default_factory=tuple)
    zero_result_queries: tuple[SearchZeroResultQuery, ...] = Field(default_factory=tuple)
    funnel_analysis: SearchFunnelAnalysis | None = None
    abandonment_analysis: SearchAbandonmentAnalysis | None = None
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchAnalyticsDashboard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    report_ids: tuple[str, ...] = Field(default_factory=tuple)
    refresh_interval_seconds: float = 300.0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchPopularQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    count: int = 0
    avg_duration_ms: float = 0.0
    click_through_rate: float = 0.0
    last_queried_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchZeroResultQuery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    count: int = 0
    last_occurrence: datetime = Field(default_factory=utc_now)
    user_ids: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchClickThrough(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    result_id: str
    result_position: int = 0
    clicked_at: datetime = Field(default_factory=utc_now)
    user_id: str = ""
    session_id: str = ""
    dwell_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchSession(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    user_id: str = ""
    status: SearchSessionStatus = SearchSessionStatus.ACTIVE
    query_count: int = 0
    click_count: int = 0
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    total_duration_ms: float = 0.0
    queries: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchAnalyticsAlert(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    metric_name: str
    threshold_value: float = 0.0
    current_value: float = 0.0
    operator: str = "gt"
    severity: str = "warning"
    message: str = ""
    triggered_at: datetime = Field(default_factory=utc_now)
    acknowledged: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFunnel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str = ""
    description: str = ""
    steps: tuple[SearchFunnelStep, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFunnelStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    order: int = 0
    description: str = ""
    event_filter: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFunnelAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    funnel_id: str
    period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    total_entries: int = 0
    step_counts: tuple[int, ...] = Field(default_factory=tuple)
    conversion_rates: tuple[float, ...] = Field(default_factory=tuple)
    overall_conversion_rate: float = 0.0
    drop_off_points: tuple[str, ...] = Field(default_factory=tuple)
    completed_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchAbandonmentAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    period: SearchMetricsPeriod = SearchMetricsPeriod.LAST_24H
    total_sessions: int = 0
    abandoned_sessions: int = 0
    abandonment_rate: float = 0.0
    avg_queries_before_abandonment: float = 0.0
    avg_session_duration_before_abandonment_ms: float = 0.0
    top_exit_queries: tuple[str, ...] = Field(default_factory=tuple)
    completed_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "SearchAbandonmentAnalysis",
    "SearchAnalyticsAlert",
    "SearchAnalyticsConfig",
    "SearchAnalyticsDashboard",
    "SearchAnalyticsReport",
    "SearchClickThrough",
    "SearchFunnel",
    "SearchFunnelAnalysis",
    "SearchFunnelStep",
    "SearchMetrics",
    "SearchMetricsPeriod",
    "SearchPerformanceReport",
    "SearchPopularQuery",
    "SearchQueryLog",
    "SearchSession",
    "SearchSessionStatus",
    "SearchTrend",
    "SearchTrendPeriod",
    "SearchZeroResultQuery",
]
