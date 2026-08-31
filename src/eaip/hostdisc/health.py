"""Health check for host discovery."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class HostDiscoveryHealthCheck:
    name: str = "hostdisc"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Host discovery service healthy",
        )


__all__ = ["HostDiscoveryHealthCheck"]
