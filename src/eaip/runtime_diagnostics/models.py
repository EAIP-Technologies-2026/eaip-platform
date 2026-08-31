"""Data models for runtime diagnostics."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ProbeType(StrEnum):
    """Type of diagnostics probe."""

    HTTP = "http"
    TCP = "tcp"
    PROCESS = "process"
    CUSTOM = "custom"


class DiagnosticsStatus(StrEnum):
    """Result status for a diagnostics probe."""

    PASS = "pass"  # noqa: S105
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class DiagnosticsReportSeverity(StrEnum):
    """Severity level for diagnostics reports and alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DiagnosticsMetricType(StrEnum):
    """Type of diagnostics metric."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class DiagnosticsCollectorStatus(StrEnum):
    """Operational status of a diagnostics collector."""

    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"


class RuntimeDiagnosticsConfig(BaseModel):
    """Configuration for the runtime diagnostics system."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    probe_interval_seconds: int = Field(default=60, ge=1)
    check_interval_seconds: int = Field(default=300, ge=1)
    snapshot_retention_days: int = Field(default=7, ge=1)
    metric_retention_days: int = Field(default=30, ge=1)
    max_alerts: int = Field(default=100, ge=1)
    max_history_entries: int = Field(default=1000, ge=1)


class DiagnosticsProbe(BaseModel):
    """A health probe that checks a specific target."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    probe_type: ProbeType
    target: str
    interval_seconds: int = Field(default=60, ge=1)
    timeout_seconds: int = Field(default=30, ge=1)
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosticsResult(BaseModel):
    """Result of a single diagnostics probe execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    probe_id: str
    status: DiagnosticsStatus
    latency_ms: float = Field(default=0.0, ge=0.0)
    message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=utc_now)


class DiagnosticsCheck(BaseModel):
    """A composite check that runs multiple probes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    probe_ids: tuple[str, ...] = Field(default=())
    interval_seconds: int = Field(default=300, ge=1)
    enabled: bool = Field(default=True)
    description: str = Field(default="")
    results: tuple[DiagnosticsResult, ...] = Field(default=())


class DiagnosticsReport(BaseModel):
    """A diagnostics report aggregating check results."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    description: str = Field(default="")
    severity: DiagnosticsReportSeverity = Field(default=DiagnosticsReportSeverity.INFO)
    checks: tuple[DiagnosticsCheck, ...] = Field(default=())
    generated_at: datetime = Field(default_factory=utc_now)
    data: dict[str, Any] = Field(default_factory=dict)


class DiagnosticsAlert(BaseModel):
    """An alert triggered by a diagnostics threshold breach."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule_name: str
    message: str
    severity: DiagnosticsReportSeverity = Field(default=DiagnosticsReportSeverity.WARNING)
    status: str = Field(default="firing")
    triggered_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None)
    details: dict[str, Any] = Field(default_factory=dict)


class DiagnosticsSnapshot(BaseModel):
    """A point-in-time snapshot of diagnostics state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    label: str
    snapshot_type: str = Field(default="full")
    data: dict[str, Any] = Field(default_factory=dict)
    taken_at: datetime = Field(default_factory=utc_now)
    size_bytes: int = Field(default=0, ge=0)


class DiagnosticsMetric(BaseModel):
    """A single diagnostics metric measurement."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: DiagnosticsMetricType
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    unit: str = Field(default="")
    recorded_at: datetime = Field(default_factory=utc_now)


class DiagnosticsDashboard(BaseModel):
    """A configurable diagnostics dashboard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    enabled: bool = Field(default=True)
    refresh_interval_seconds: int = Field(default=60, ge=1)
    widgets: tuple[dict[str, Any], ...] = Field(default=())


class DiagnosticsCollector(BaseModel):
    """A diagnostics data collector instance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    collector_type: str = Field(default="default")
    status: DiagnosticsCollectorStatus = Field(default=DiagnosticsCollectorStatus.STOPPED)
    config: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = Field(default=None)
    stopped_at: datetime | None = Field(default=None)


class DiagnosticsHistoryEntry(BaseModel):
    """An entry in the diagnostics audit history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    action: str
    component: str
    message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=utc_now)
    severity: DiagnosticsReportSeverity = Field(default=DiagnosticsReportSeverity.INFO)


class DiagnosticsThreshold(BaseModel):
    """A threshold definition for diagnostics metric alerting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_name: str
    warning_threshold: float = Field(default=0.0)
    critical_threshold: float = Field(default=0.0)
    operator: str = Field(default="gt")
    enabled: bool = Field(default=True)


__all__ = [
    "DiagnosticsAlert",
    "DiagnosticsCheck",
    "DiagnosticsCollector",
    "DiagnosticsCollectorStatus",
    "DiagnosticsDashboard",
    "DiagnosticsHistoryEntry",
    "DiagnosticsMetric",
    "DiagnosticsMetricType",
    "DiagnosticsProbe",
    "DiagnosticsReport",
    "DiagnosticsReportSeverity",
    "DiagnosticsResult",
    "DiagnosticsSnapshot",
    "DiagnosticsStatus",
    "DiagnosticsThreshold",
    "ProbeType",
    "RuntimeDiagnosticsConfig",
]
