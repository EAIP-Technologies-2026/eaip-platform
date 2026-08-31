"""Data models for report scheduling — definitions, executions, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ReportFormat(StrEnum):
    """Supported output formats for reports."""

    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"


class ReportDefinition(BaseModel):
    """A scheduled report definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    report_type: str
    format: ReportFormat = Field(default=ReportFormat.PDF)
    schedule_cron: str = Field(default="0 0 * * *")
    recipients: tuple[str, ...] = Field(default=())
    parameters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)


class ReportExecution(BaseModel):
    """A single execution record for a scheduled report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    report_id: str
    status: str = Field(default="pending")
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    output_path: str = Field(default="")
    error: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)


class SchedulerConfig(BaseModel):
    """Configuration for the report scheduler."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_concurrent_executions: int = Field(default=5, ge=1)
    default_recipients: tuple[str, ...] = Field(default=())
    output_directory: str = Field(default="/tmp/reports")
    max_retries: int = Field(default=3, ge=0)


__all__ = [
    "ReportDefinition",
    "ReportExecution",
    "ReportFormat",
    "SchedulerConfig",
]
