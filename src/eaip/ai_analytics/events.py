"""AI Analytics domain events — published via EventBus during AI analytics operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class AiAnalyticsConfigUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.config.updated"
    changes: dict[str, Any] = {}
    previous_config: dict[str, Any] = {}


class AiAnalyticsMetricRecorded(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.metric.recorded"
    metric_id: str = ""
    metric_type: str = ""
    value: float = 0.0
    model_id: str = ""
    deployment_id: str = ""
    tags: dict[str, str] = {}


class AiAnalyticsReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.report.generated"
    report_id: str = ""
    name: str = ""
    period: str = ""
    model_ids: tuple[str, ...] = ()
    deployment_ids: tuple[str, ...] = ()
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None


class AiAnalyticsDashboardCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.dashboard.created"
    dashboard_id: str = ""
    name: str = ""
    widget_count: int = 0


class AiAnalyticsDashboardUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.dashboard.updated"
    dashboard_id: str = ""
    changes: dict[str, Any] = {}
    previous_version: int = 0


class AiAnomalyDetected(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.anomaly.detected"
    metric_id: str = ""
    model_id: str = ""
    deployment_id: str = ""
    value: float = 0.0
    expected_value: float = 0.0
    deviation: float = 0.0
    severity: str = ""


class AiAnalyticsTrendComputed(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.trend.computed"
    metric_id: str = ""
    model_id: str = ""
    deployment_id: str = ""
    direction: str = ""
    change_percent: float = 0.0
    confidence: float = 0.0


class AiAnalyticsForecastGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.forecast.generated"
    forecast_id: str = ""
    metric_id: str = ""
    model_id: str = ""
    deployment_id: str = ""
    horizon_hours: float = 0.0
    point_count: int = 0


class AiAnalyticsInsightGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.insight.generated"
    insight_id: str = ""
    title: str = ""
    severity: str = ""
    metric_ids: tuple[str, ...] = ()
    model_ids: tuple[str, ...] = ()


class AiAnalyticsExportCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.export.completed"
    export_id: str = ""
    report_id: str = ""
    format: str = ""
    destination: str = ""
    record_count: int = 0
    success: bool = True


class AiModelUsageReported(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.model_usage.reported"
    model_id: str = ""
    deployment_id: str = ""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    peak_concurrent: int = 0


class AiTokenUsageReported(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.token_usage.reported"
    model_id: str = ""
    deployment_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


class AiLatencyReported(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.latency.reported"
    model_id: str = ""
    deployment_id: str = ""
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0


class AiErrorRateReported(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.error_rate.reported"
    model_id: str = ""
    deployment_id: str = ""
    error_rate: float = 0.0
    total_errors: int = 0


class AiCostReported(DomainEvent):
    event_type: ClassVar[str] = "eaip.ai_analytics.cost.reported"
    model_id: str = ""
    deployment_id: str = ""
    total_cost: float = 0.0
    currency: str = "USD"


AiAnalyticsEvent = (
    AiAnalyticsConfigUpdated
    | AiAnalyticsMetricRecorded
    | AiAnalyticsReportGenerated
    | AiAnalyticsDashboardCreated
    | AiAnalyticsDashboardUpdated
    | AiAnomalyDetected
    | AiAnalyticsTrendComputed
    | AiAnalyticsForecastGenerated
    | AiAnalyticsInsightGenerated
    | AiAnalyticsExportCompleted
    | AiModelUsageReported
    | AiTokenUsageReported
    | AiLatencyReported
    | AiErrorRateReported
    | AiCostReported
)


__all__ = [
    "AiAnalyticsConfigUpdated",
    "AiAnalyticsDashboardCreated",
    "AiAnalyticsDashboardUpdated",
    "AiAnalyticsEvent",
    "AiAnalyticsExportCompleted",
    "AiAnalyticsForecastGenerated",
    "AiAnalyticsInsightGenerated",
    "AiAnalyticsMetricRecorded",
    "AiAnalyticsReportGenerated",
    "AiAnalyticsTrendComputed",
    "AiAnomalyDetected",
    "AiCostReported",
    "AiErrorRateReported",
    "AiLatencyReported",
    "AiModelUsageReported",
    "AiTokenUsageReported",
]
