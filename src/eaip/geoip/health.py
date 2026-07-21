"""Health check for Geo-IP service."""

from __future__ import annotations

from eaip.geoip.service import GeoIPService
from eaip.health.checks import HealthReport, HealthStatus


class GeoIPHealthCheck:
    name: str = "geoip"

    def __init__(self, service: GeoIPService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            records = await self._service.list_records()
            details["cached_records"] = len(records)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Geo-IP service unavailable: {exc}",
                details={"error": str(exc)},
            )

        total_lookups = sum(r.lookup_count for r in records)
        details["total_lookups"] = total_lookups

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        blocked_countries = details.get("blocked_countries")
        if isinstance(blocked_countries, (list, tuple)) and len(blocked_countries) > 0:
            messages.append("Geo-blocking active")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Geo-IP service healthy",
            details=details,
        )


__all__ = ["GeoIPHealthCheck"]
