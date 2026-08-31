"""Data models for Helm chart repository — charts, releases, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class HelmChartStatus(StrEnum):
    STORED = "stored"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ReleaseStatus(StrEnum):
    DEPLOYED = "deployed"
    UPGRADED = "upgraded"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class HelmChart(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    version: str
    app_version: str = Field(default="")
    description: str = Field(default="")
    chart_data_ref: str
    status: HelmChartStatus = Field(default=HelmChartStatus.STORED)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ChartRelease(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    chart_id: str
    target_environment: str
    values: dict[str, object] = Field(default_factory=dict)
    revision: int = Field(default=1)
    status: ReleaseStatus = Field(default=ReleaseStatus.DEPLOYED)
    deployed_at: datetime = Field(default_factory=utc_now)


class HelmConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_url: str = Field(default="")
    storage_backend: str = Field(default="local")
    max_versions_per_chart: int = Field(default=50, ge=1)
    default_timeout_seconds: int = Field(default=300, ge=1)


__all__ = [
    "ChartRelease",
    "HelmChart",
    "HelmChartStatus",
    "HelmConfig",
    "ReleaseStatus",
]
