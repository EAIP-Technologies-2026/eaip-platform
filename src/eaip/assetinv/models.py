"""Data models for asset inventory — assets, categories, status, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class AssetStatus(StrEnum):
    """Lifecycle status of an asset."""

    ACTIVE = "active"
    DECOMMISSIONED = "decommissioned"
    MAINTENANCE = "maintenance"
    LOST = "lost"


class AssetCategory(BaseModel):
    """A category classification for assets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")


class Asset(BaseModel):
    """A single inventory asset record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: str
    category: str = Field(default="")
    status: AssetStatus = Field(default=AssetStatus.ACTIVE)
    location: str = Field(default="")
    purchase_date: datetime | None = Field(default=None)
    purchase_cost: float = Field(default=0, ge=0)
    current_value: float = Field(default=0, ge=0)
    department: str = Field(default="")
    owner: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InventoryConfig(BaseModel):
    """Configuration for the asset inventory service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    default_department: str = Field(default="general")
    depreciation_rate: float = Field(default=0.1, ge=0, le=1)
    notify_on_decommission: bool = Field(default=True)


__all__ = [
    "Asset",
    "AssetCategory",
    "AssetStatus",
    "InventoryConfig",
]
