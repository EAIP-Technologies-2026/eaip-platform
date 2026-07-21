"""Domain models for workflow monitoring — status, alerts, dashboards, thresholds."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class WorkflowMonitorStatus(StrEnum):
    """Enumeration of possible workflow monitor statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"
    ARCHIVED = "archived"


class AlertSeverity(StrEnum):
    """Enumeration of alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MonitorMetricPoint(BaseModel):
    """A single metric data point captured during monitoring."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    source: str = ""


class MonitorTimeSeries(BaseModel):
    """A time series collection of metric data points."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_name: str
    points: tuple[MonitorMetricPoint, ...] = Field(default_factory=tuple)
    start_time: datetime
    end_time: datetime
    interval_seconds: float = 60.0


class MonitorThreshold(BaseModel):
    """A threshold rule that triggers alerts when breached."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    metric_name: str
    operator: str = "gt"
    value: float
    severity: AlertSeverity = AlertSeverity.MEDIUM
    duration_seconds: float = 0.0
    description: str = ""
    enabled: bool = True


class MonitorNotificationChannel(BaseModel):
    """A notification channel for alert delivery (email, slack, etc.)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: str = "email"
    target: str = ""
    enabled: bool = True


class WorkflowMonitorConfig(BaseModel):
    """Configuration for monitoring a specific workflow."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    workflow_name: str
    description: str = ""
    status: WorkflowMonitorStatus = WorkflowMonitorStatus.ACTIVE
    thresholds: tuple[MonitorThreshold, ...] = Field(default_factory=tuple)
    notification_channels: tuple[MonitorNotificationChannel, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class WorkflowMonitorSnapshot(BaseModel):
    """A point-in-time snapshot of workflow monitor state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    config_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    status: WorkflowMonitorStatus = WorkflowMonitorStatus.ACTIVE
    metrics: dict[str, float] = Field(default_factory=dict)
    active_alerts: tuple[str, ...] = Field(default_factory=tuple)
    healthy: bool = True
    message: str = ""


class WorkflowMonitorAlert(BaseModel):
    """An alert raised when a monitored threshold is breached."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    config_id: str
    severity: AlertSeverity = AlertSeverity.MEDIUM
    metric_name: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    message: str = ""
    triggered_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None
    acknowledged: bool = False


class WorkflowMonitorDashboard(BaseModel):
    """A dashboard that displays monitor data and widgets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    config_ids: tuple[str, ...] = Field(default_factory=tuple)
    widgets: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    refresh_interval_seconds: float = 60.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "AlertSeverity",
    "MonitorMetricPoint",
    "MonitorNotificationChannel",
    "MonitorThreshold",
    "MonitorTimeSeries",
    "WorkflowMonitorAlert",
    "WorkflowMonitorConfig",
    "WorkflowMonitorDashboard",
    "WorkflowMonitorSnapshot",
    "WorkflowMonitorStatus",
]
