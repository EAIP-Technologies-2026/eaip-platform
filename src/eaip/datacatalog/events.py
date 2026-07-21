"""Domain events for the enterprise data catalog."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class AssetRegistered(DomainEvent):
    """Emitted when a new data asset is registered."""

    event_type: ClassVar[str] = "eaip.datacatalog.asset.registered"

    asset_id: str
    name: str
    asset_type: str
    source_id: str


class AssetUpdated(DomainEvent):
    """Emitted when a data asset is updated."""

    event_type: ClassVar[str] = "eaip.datacatalog.asset.updated"

    asset_id: str
    name: str
    changes: dict[str, Any]


class AssetRemoved(DomainEvent):
    """Emitted when a data asset is removed from the catalog."""

    event_type: ClassVar[str] = "eaip.datacatalog.asset.removed"

    asset_id: str
    name: str
    reason: str = ""


__all__ = [
    "AssetRegistered",
    "AssetRemoved",
    "AssetUpdated",
]
