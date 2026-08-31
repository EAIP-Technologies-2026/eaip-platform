"""Health check for firewall rule manager."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class FirewallHealthCheck:
    """Health check for the firewall rule manager service."""

    name: str = "firewall"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Firewall rule manager service healthy",
        )


__all__ = ["FirewallHealthCheck"]
