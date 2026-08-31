"""Analytics domain models — metric definitions, time series, reports, trends, dashboards."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class MetricType(StrEnum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AggregationType(StrEnum):
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    LATEST = "latest"
    P50 = "p50"
    P95 = "p95"
    P99 = "p99"


class TrendDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"


class WidgetType(StrEnum):
    TIMESERIES = "timeseries"
    COUNTER = "counter"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    TABLE = "table"


class MetricDefinition(BaseModel):
    """Definition of a single metric that can be recorded and queried."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    type: MetricType = MetricType.COUNTER
    unit: str = ""
    aggregation: AggregationType = AggregationType.SUM
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class MetricPoint(BaseModel):
    """A single recorded data point for a metric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    timestamp: datetime
    value: float
    tags: dict[str, str] = Field(default_factory=dict)
    source: str = ""
    labels: dict[str, str] = Field(default_factory=dict)


class TimeSeriesPoint(BaseModel):
    """A single point in a time series result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime
    value: float
    label: str = ""


class TimeSeriesResult(BaseModel):
    """The result of a time series query for a single metric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    points: tuple[TimeSeriesPoint, ...] = Field(default_factory=tuple)
    aggregation: AggregationType = AggregationType.SUM
    start_time: datetime
    end_time: datetime
    interval_seconds: float = 60.0


class AnalyticsReport(BaseModel):
    """A complete analytics report covering one or more metrics over a time range."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    metric_ids: tuple[str, ...] = Field(default_factory=tuple)
    time_range: tuple[datetime, datetime]
    interval: float = 60.0
    results: dict[str, TimeSeriesResult] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrendAnalysis(BaseModel):
    """Result of a trend analysis for a single metric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    direction: TrendDirection = TrendDirection.STABLE
    change_percent: float = 0.0
    confidence: float = 0.0
    period_comparison: dict[str, float] = Field(default_factory=dict)
    forecast_values: tuple[float, ...] = Field(default_factory=tuple)
    seasonality_detected: bool = False
    anomaly_count: int = 0


class DashboardWidget(BaseModel):
    """A single widget on a dashboard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: WidgetType = WidgetType.TIMESERIES
    metric_ids: tuple[str, ...] = Field(default_factory=tuple)
    title: str = ""
    width: int = 1
    height: int = 1
    config: dict[str, Any] = Field(default_factory=dict)


class DashboardDefinition(BaseModel):
    """Definition of a dashboard containing multiple widgets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    widgets: tuple[DashboardWidget, ...] = Field(default_factory=tuple)
    refresh_interval_seconds: float = 60.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsConfig(BaseModel):
    """Configuration for the analytics subsystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    retention_days: int = 90
    aggregation_interval_seconds: float = 60.0
    max_data_points: int = 10000
    enable_trend_detection: bool = True
    enable_anomaly_detection: bool = True


__all__ = [
    "AggregationType",
    "AnalyticsConfig",
    "AnalyticsReport",
    "DashboardDefinition",
    "DashboardWidget",
    "MetricDefinition",
    "MetricPoint",
    "MetricType",
    "TimeSeriesPoint",
    "TimeSeriesResult",
    "TrendAnalysis",
    "TrendDirection",
    "WidgetType",
]
