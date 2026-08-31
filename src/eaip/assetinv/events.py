"""Domain events for asset inventory."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.assetinv.models import AssetStatus
from eaip.events.event import DomainEvent


class AssetRegistered(DomainEvent):
    """Emitted when a new asset is registered."""

    event_type: ClassVar[str] = "eaip.assetinv.asset.registered"

    asset_id: str
    name: str
    asset_type: str
    department: str


class AssetUpdated(DomainEvent):
    """Emitted when an existing asset is updated."""

    event_type: ClassVar[str] = "eaip.assetinv.asset.updated"

    asset_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class AssetDecommissioned(DomainEvent):
    """Emitted when an asset is decommissioned."""

    event_type: ClassVar[str] = "eaip.assetinv.asset.decommissioned"

    asset_id: str
    previous_status: AssetStatus
    reason: str = Field(default="")


__all__ = [
    "AssetDecommissioned",
    "AssetRegistered",
    "AssetUpdated",
]
