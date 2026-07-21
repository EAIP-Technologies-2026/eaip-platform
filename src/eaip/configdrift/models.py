"""Data models for the configuration drift detection service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ConfigSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    config_data: dict[str, Any]
    checksum: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)


class DriftReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    baseline_id: str
    current_id: str
    differences: list[dict[str, Any]] = Field(default_factory=list)
    severity: str = Field(default="info")
    detected_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None)
    resolved: bool = Field(default=False)


class DriftRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    resource_type: str = Field(default="*")
    path: str = Field(default="")
    severity: str = Field(default="warning")
    enabled: bool = Field(default=True)


class DriftConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scan_interval_minutes: int = Field(default=60, ge=1)
    max_differences_per_report: int = Field(default=100, ge=1)
    default_severity: str = Field(default="warning")
    excluded_paths: list[str] = Field(default_factory=list)


__all__ = [
    "ConfigSnapshot",
    "DriftConfig",
    "DriftReport",
    "DriftRule",
]
