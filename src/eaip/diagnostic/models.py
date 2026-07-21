"""Data models for diagnostic data collection."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DiagnosticReport(BaseModel):
    """A single diagnostic data report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    component: str
    category: str
    data: dict[str, Any] = Field(default_factory=dict)
    severity: DiagnosticSeverity = Field(default=DiagnosticSeverity.INFO)
    collected_at: datetime = Field(default_factory=utc_now)
    source: str = Field(default="")


class CollectionRule(BaseModel):
    """A rule defining what diagnostic data to collect and how often."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    component: str
    metric_path: str
    interval_seconds: int = Field(default=60, ge=1)
    enabled: bool = Field(default=True)


class CollectorConfig(BaseModel):
    """Configuration for the diagnostic collector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_reports: int = Field(default=1000, ge=1)
    default_interval_seconds: int = Field(default=60, ge=1)
    retention_days: int = Field(default=30, ge=1)


__all__ = [
    "CollectionRule",
    "CollectorConfig",
    "DiagnosticReport",
    "DiagnosticSeverity",
]
