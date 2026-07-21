from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now

WidgetType = Literal["timeseries", "gauge", "heatmap", "table", "stat", "alert_list"]
AlertCondition = Literal["gt", "gte", "lt", "lte", "eq", "neq"]
AlertSeverity = Literal["info", "warning", "critical"]
SloStatus = Literal["active", "paused", "at_risk", "violated"]
NotificationChannelType = Literal["email", "slack", "webhook", "pagerduty"]


class DataPoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


class DashboardWidget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: WidgetType
    title: str
    metric_sources: tuple[str, ...] = Field(default=())
    width: int = 4
    height: int = 4
    config: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, Any] = Field(default_factory=dict)


class ObservabilityDashboard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    widgets: tuple[DashboardWidget, ...] = Field(default=())
    refresh_interval_seconds: int = 60
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class NotificationChannel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: NotificationChannelType
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    metric_name: str
    condition: AlertCondition
    threshold: float
    evaluation_window_seconds: int = 300
    evaluation_frequency_seconds: int = 60
    severity: AlertSeverity = "warning"
    notification_channels: tuple[str, ...] = Field(default=())
    enabled: bool = True
    cooldown_seconds: int = 600
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertInstance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule_id: str
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    condition: AlertCondition
    severity: AlertSeverity
    message: str = ""
    status: str = "firing"  # firing / acknowledged / resolved
    fired_at: datetime = Field(default_factory=utc_now)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SliDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    metric_source: str
    good_events_filter: str = ""
    total_events_filter: str = ""
    calculation_method: str = "ratio"  # ratio / percentile
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServiceLevelObjective(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    sli_definition_id: str = ""
    target_value: float
    target_percent: float = 99.9
    window_seconds: int = 604800  # 7 days
    burn_rate_threshold: float = 2.0
    alert_on_burn_rate: bool = True
    status: SloStatus = "active"
    current_value: float = 100.0
    current_burn_rate: float = 0.0
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservabilityConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_interval_seconds: int = 60
    alert_cooldown_default_seconds: int = 600
    dashboard_refresh_default: int = 60
    slo_evaluation_interval: int = 300
    max_alerts_per_rule: int = 100


__all__ = [
    "AlertCondition",
    "AlertInstance",
    "AlertRule",
    "AlertSeverity",
    "DashboardWidget",
    "DataPoint",
    "NotificationChannel",
    "NotificationChannelType",
    "ObservabilityConfig",
    "ObservabilityDashboard",
    "ServiceLevelObjective",
    "SliDefinition",
    "SloStatus",
    "WidgetType",
]
