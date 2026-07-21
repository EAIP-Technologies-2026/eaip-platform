"""Geo-IP Service — IP geolocation lookup, geo-blocking, cache management, and enrichment."""

from __future__ import annotations

from eaip.geoip.events import (
    CacheUpdated,
    GeoBlockTriggered,
    LookupPerformed,
)
from eaip.geoip.exceptions import (
    GeoIPError,
    LookupError,
)
from eaip.geoip.health import GeoIPHealthCheck
from eaip.geoip.integration import GeoIPRuntimeModule
from eaip.geoip.models import (
    GeoIPConfig,
    GeoIPLookup,
    GeoIPRecord,
    LookupResultType,
)
from eaip.geoip.service import GeoIPService

__all__ = [
    "CacheUpdated",
    "GeoBlockTriggered",
    "GeoIPConfig",
    "GeoIPError",
    "GeoIPHealthCheck",
    "GeoIPLookup",
    "GeoIPRecord",
    "GeoIPRuntimeModule",
    "GeoIPService",
    "LookupError",
    "LookupPerformed",
    "LookupResultType",
]
