"""Data models for the enterprise data catalog."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AssetType(StrEnum):
    """Types of data assets in the catalog."""

    TABLE = "table"
    VIEW = "view"
    FILE = "file"
    STREAM = "stream"
    API = "api"
    MODEL = "model"
    DASHBOARD = "dashboard"
    REPORT = "report"


class DataSource(BaseModel):
    """A source system from which data assets originate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_type: str
    connection_string: str = Field(default="")
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataAsset(BaseModel):
    """A registered data asset in the catalog."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    asset_type: AssetType
    source_id: str
    description: str = Field(default="")
    schema_: dict[str, str] = Field(default_factory=dict, alias="schema")
    tags: tuple[str, ...] = Field(default=())
    lineage: tuple[str, ...] = Field(default=())
    owner: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogConfig(BaseModel):
    """Configuration for the data catalog."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    auto_discovery_enabled: bool = Field(default=True)
    discovery_interval_seconds: int = Field(default=86400, ge=60)
    max_assets_per_source: int = Field(default=10000, ge=1)
    enable_lineage_tracking: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300, ge=0)


__all__ = [
    "AssetType",
    "CatalogConfig",
    "DataAsset",
    "DataSource",
]
