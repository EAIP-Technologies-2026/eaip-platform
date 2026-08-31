"""Data models for the custom dashboard builder."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class WidgetType(StrEnum):
    CHART = "chart"
    TABLE = "table"
    METRIC = "metric"
    TEXT = "text"


class WidgetDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    widget_type: WidgetType
    title: str
    config: dict[str, Any] = Field(default_factory=dict)
    position: tuple[int, int] = Field(default=(0, 0))
    size: tuple[int, int] = Field(default=(1, 1))


class DashboardLayout(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    columns: int = Field(default=12, ge=1, le=24)
    rows: int = Field(default=12, ge=1, le=24)


class DashboardConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    refresh_interval_seconds: int = Field(default=30, ge=0)
    layout: DashboardLayout = Field(default_factory=DashboardLayout)
    theme: str = Field(default="default")


class Dashboard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    widgets: tuple[WidgetDefinition, ...] = Field(default=())
    config: DashboardConfig = Field(default_factory=DashboardConfig)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Dashboard",
    "DashboardConfig",
    "DashboardLayout",
    "WidgetDefinition",
    "WidgetType",
]
