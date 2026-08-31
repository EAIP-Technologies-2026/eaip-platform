"""Geo-IP service — IP geolocation lookups, caching, and geo-blocking."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.geoip.events import (
    CacheUpdated,
    GeoBlockTriggered,
    LookupPerformed,
)
from eaip.geoip.models import (
    GeoIPConfig,
    GeoIPLookup,
    GeoIPRecord,
    LookupResultType,
)

EventCallback = Callable[[Any], Any]


class GeoIPService:
    def __init__(
        self,
        config: GeoIPConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or GeoIPConfig()
        self._records: dict[str, GeoIPRecord] = {}
        self._lookups: dict[str, GeoIPLookup] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    # -- Geo-IP Lookup -------------------------------------------------------

    async def lookup(self, ip: str) -> GeoIPLookup:
        if self._is_blocked(ip):
            lookup = GeoIPLookup(
                id=str(uuid.uuid4()),
                ip=ip,
                result=LookupResultType.BLOCKED,
            )
            self._lookups[lookup.id] = lookup
            self._emit(
                GeoBlockTriggered(
                    ip=ip,
                    country=self._guess_country(ip),
                    reason="IP is in blocked country list",
                )
            )
            self._emit(
                LookupPerformed(
                    ip=ip,
                    record_id="",
                    result=lookup.result.value,
                )
            )
            return lookup

        record = await self._resolve(ip)

        updated_record = GeoIPRecord(
            ip=record.ip,
            country=record.country,
            region=record.region,
            city=record.city,
            latitude=record.latitude,
            longitude=record.longitude,
            isp=record.isp,
            asn=record.asn,
            timezone=record.timezone,
            lookup_count=record.lookup_count + 1,
        )
        self._records[record.ip] = updated_record

        lookup = GeoIPLookup(
            id=str(uuid.uuid4()),
            ip=ip,
            record_id=record.ip,
            lookup_type="geolocation",
            result=LookupResultType.HIT,
        )
        self._lookups[lookup.id] = lookup
        self._emit(
            LookupPerformed(
                ip=ip,
                record_id=record.ip,
                result=lookup.result.value,
            )
        )
        return lookup

    async def _resolve(self, ip: str) -> GeoIPRecord:
        if ip in self._records:
            return self._records[ip]

        record = GeoIPRecord(
            ip=ip,
            country=self._guess_country(ip),
            region="Default Region",
            city="Default City",
            latitude=self._config.default_latitude,
            longitude=self._config.default_longitude,
            isp="Default ISP",
            asn="AS00000",
            timezone="UTC",
        )
        self._records[ip] = record
        return record

    def _guess_country(self, ip: str) -> str:
        if ip.startswith("10.") or ip.startswith("192.168."):
            return "PRIVATE"
        if ip.startswith("198.51."):
            return "BLOCKED"
        return "US"

    def _is_blocked(self, ip: str) -> bool:
        if not self._config.enable_geo_blocking:
            return False
        country = self._guess_country(ip)
        return country in self._config.blocked_countries

    # -- Record management ---------------------------------------------------

    async def get_record(self, ip: str) -> GeoIPRecord:
        if ip not in self._records:
            return await self._resolve(ip)
        return self._records[ip]

    async def list_records(self) -> list[GeoIPRecord]:
        return list(self._records.values())

    async def upsert_record(self, record: GeoIPRecord) -> GeoIPRecord:
        self._records[record.ip] = record
        return record

    async def clear_cache(self) -> int:
        size = len(self._records)
        self._records.clear()
        self._emit(
            CacheUpdated(
                cache_size=0,
                action="cleared",
            )
        )
        return size

    # -- Lookup history ------------------------------------------------------

    async def get_lookup(self, lookup_id: str) -> GeoIPLookup:
        if lookup_id not in self._lookups:
            raise RuntimeError(f"Lookup not found: {lookup_id}")
        return self._lookups[lookup_id]

    async def list_lookups(
        self,
        ip: str | None = None,
        result: LookupResultType | None = None,
    ) -> list[GeoIPLookup]:
        result_list = list(self._lookups.values())
        if ip:
            result_list = [l for l in result_list if l.ip == ip]
        if result:
            result_list = [l for l in result_list if l.result == result]
        return result_list


__all__ = ["GeoIPService"]
