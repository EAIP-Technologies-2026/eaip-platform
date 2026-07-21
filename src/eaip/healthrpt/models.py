"""Pydantic models for the enterprise health reporter."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.health.checks import HealthStatus
from eaip.shared.time import utc_now


class ComponentSummary(BaseModel):
    """Summary of a single component's health."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    component_id: str = Field(description="Unique identifier for the component")
    component_name: str = Field(description="Human-readable component name")
    status: HealthStatus = Field(description="Current health status")
    check_count: int = Field(default=0, ge=0, description="Number of health checks performed")
    pass_count: int = Field(default=0, ge=0, description="Number of passed checks")
    fail_count: int = Field(default=0, ge=0, description="Number of failed checks")
    last_checked_at: datetime | None = Field(
        default=None, description="When the component was last checked"
    )
    uptime_percentage: float = Field(
        default=100.0, ge=0.0, le=100.0, description="Uptime percentage"
    )


class SLAResult(BaseModel):
    """SLA compliance result for a component."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    component_id: str = Field(description="Component this result applies to")
    sla_target: float = Field(default=99.9, ge=0.0, le=100.0, description="SLA target percentage")
    actual_achievement: float = Field(
        default=100.0, ge=0.0, le=100.0, description="Actual achievement percentage"
    )
    compliant: bool = Field(default=True, description="Whether the SLA target was met")
    period_start: datetime = Field(description="Start of the SLA measurement period")
    period_end: datetime = Field(description="End of the SLA measurement period")


class HealthReport(BaseModel):
    """A comprehensive health report for the enterprise platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_id: str = Field(description="Unique identifier for this report")
    generated_at: datetime = Field(
        default_factory=utc_now, description="When the report was generated"
    )
    period_start: datetime = Field(description="Start of the reporting period")
    period_end: datetime = Field(description="End of the reporting period")
    component_summaries: tuple[ComponentSummary, ...] = Field(
        default=(),
        description="Health summaries for each component",
    )
    overall_status: HealthStatus = Field(
        default=HealthStatus.HEALTHY, description="Overall platform health status"
    )
    sla_achievement: float = Field(
        default=100.0, ge=0.0, le=100.0, description="Overall SLA achievement percentage"
    )


class ReporterConfig(BaseModel):
    """Configuration for the enterprise health reporter."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_interval_hours: int = Field(
        default=24, ge=1, description="Interval between automated reports"
    )
    sla_target_percentage: float = Field(
        default=99.9, ge=0.0, le=100.0, description="Default SLA target"
    )
    history_retention_days: int = Field(
        default=365, ge=1, description="Days to retain report history"
    )
    enable_auto_reports: bool = Field(
        default=True, description="Whether to generate reports automatically"
    )
    degrade_threshold: float = Field(
        default=95.0, ge=0.0, le=100.0, description="SLA percentage that triggers DEGRADED status"
    )
    unhealthy_threshold: float = Field(
        default=90.0, ge=0.0, le=100.0, description="SLA percentage that triggers UNHEALTHY status"
    )


__all__ = [
    "ComponentSummary",
    "HealthReport",
    "ReporterConfig",
    "SLAResult",
]
