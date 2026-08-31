"""Health check for floating license management."""

from __future__ import annotations

from eaip.floatlicense.manager import FloatingLicenseManager
from eaip.health.checks import HealthReport, HealthStatus


class FloatLicenseHealthCheck:
    name: str = "floatlicense"

    def __init__(self, manager: FloatingLicenseManager) -> None:
        self._manager = manager

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            pools = await self._manager.list_pools()
            details["pool_count"] = len(pools)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Floating license manager unavailable: {exc}",
                details={"error": str(exc)},
            )

        total_avail = sum(p.available_licenses for p in pools)
        total_total = sum(p.total_licenses for p in pools)
        details["total_licenses"] = total_total
        details["available_licenses"] = total_avail

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if total_avail == 0 and total_total > 0:
            status = HealthStatus.DEGRADED
            messages.append("All licenses are checked out")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Floating license management healthy",
            details=details,
        )


__all__ = ["FloatLicenseHealthCheck"]
