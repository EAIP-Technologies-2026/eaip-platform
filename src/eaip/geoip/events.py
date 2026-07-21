"""Domain events for Geo-IP service."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class LookupPerformed(DomainEvent):
    event_type: ClassVar[str] = "eaip.geoip.lookup_performed"

    ip: str
    record_id: str
    result: str


class GeoBlockTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.geoip.geo_block_triggered"

    ip: str
    country: str
    reason: str


class CacheUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.geoip.cache_updated"

    cache_size: int
    action: str


__all__ = [
    "CacheUpdated",
    "GeoBlockTriggered",
    "LookupPerformed",
]
