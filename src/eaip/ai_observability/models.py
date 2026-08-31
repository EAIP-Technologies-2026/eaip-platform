from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SpanKind(StrEnum):
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class AiTraceSpanStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
    UNKNOWN = "unknown"


class MetricType(StrEnum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AiObservabilityAlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


class TokenUsage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LatencyBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ttft_ms: float = 0.0
    prompt_processing_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0


class AiTraceSpan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    span_id: str
    trace_id: str
    parent_span_id: str | None = None
    name: str
    kind: SpanKind = SpanKind.INTERNAL
    status: AiTraceSpanStatus = AiTraceSpanStatus.OK
    start_time: datetime = Field(default_factory=utc_now)
    end_time: datetime | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: tuple[AiObservabilityEvent, ...] = Field(default=())


class AiTraceContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    baggage: dict[str, str] = Field(default_factory=dict)


class AiObservabilityEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=utc_now)
    attributes: dict[str, Any] = Field(default_factory=dict)


class AiModelCallMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    latency: LatencyBreakdown = Field(default_factory=LatencyBreakdown)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_usd: float = 0.0
    retry_count: int = 0
    cache_hit: bool = False


class AiModelCall(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: str
    model_name: str
    provider: str
    deployment_name: str = ""
    input: str = ""
    output: str = ""
    metrics: AiModelCallMetrics = Field(default_factory=AiModelCallMetrics)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class AiObservabilityMetric(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: MetricType
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
    unit: str = ""


class AiObservabilityReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    report_id: str
    title: str
    description: str = ""
    period_start: datetime
    period_end: datetime
    traces: tuple[AiTraceSpan, ...] = Field(default=())
    model_calls: tuple[AiModelCall, ...] = Field(default=())
    metrics: tuple[AiObservabilityMetric, ...] = Field(default=())
    alerts: tuple[AiObservabilityAlert, ...] = Field(default=())
    summary: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)


class AiObservabilityDashboard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    widgets: tuple[dict[str, Any], ...] = Field(default=())
    refresh_interval_seconds: int = 60
    tags: tuple[str, ...] = Field(default=())
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AiObservabilityAlert(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    alert_id: str
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    severity: AiObservabilityAlertSeverity = AiObservabilityAlertSeverity.WARNING
    message: str = ""
    status: str = "firing"
    fired_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AiObservabilityConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tracing_enabled: bool = True
    metrics_enabled: bool = True
    reporting_enabled: bool = True
    alerting_enabled: bool = True
    sampling_rate: float = 1.0
    max_traces: int = 1000
    max_model_calls: int = 5000
    report_interval_seconds: int = 3600


__all__ = [
    "AiModelCall",
    "AiModelCallMetrics",
    "AiObservabilityAlert",
    "AiObservabilityAlertSeverity",
    "AiObservabilityConfig",
    "AiObservabilityDashboard",
    "AiObservabilityEvent",
    "AiObservabilityMetric",
    "AiObservabilityReport",
    "AiTraceContext",
    "AiTraceSpan",
    "AiTraceSpanStatus",
    "LatencyBreakdown",
    "MetricType",
    "SpanKind",
    "TokenUsage",
]
