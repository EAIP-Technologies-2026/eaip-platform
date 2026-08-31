"""Data models for Geo-IP service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class LookupResultType(StrEnum):
    HIT = "hit"
    MISS = "miss"
    BLOCKED = "blocked"


class GeoIPRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ip: str
    country: str = Field(default="")
    region: str = Field(default="")
    city: str = Field(default="")
    latitude: float = Field(default=0.0)
    longitude: float = Field(default=0.0)
    isp: str = Field(default="")
    asn: str = Field(default="")
    timezone: str = Field(default="")
    lookup_count: int = Field(default=0, ge=0)


class GeoIPLookup(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    ip: str
    record_id: str = Field(default="")
    lookup_type: str = Field(default="")
    result: LookupResultType
    looked_up_at: datetime = Field(default_factory=utc_now)


class GeoIPConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    cache_ttl_seconds: int = Field(default=3600, ge=1)
    max_cache_size: int = Field(default=10000, ge=1)
    blocked_countries: tuple[str, ...] = Field(default=())
    enable_geo_blocking: bool = Field(default=True)
    default_latitude: float = Field(default=0.0)
    default_longitude: float = Field(default=0.0)


__all__ = [
    "GeoIPConfig",
    "GeoIPLookup",
    "GeoIPRecord",
    "LookupResultType",
]
