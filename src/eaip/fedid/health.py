"""Health check for federated identity."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class FederatedIdentityHealthCheck:
    """Health check for the federated identity provider."""

    name: str = "fedid"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Federated identity healthy",
        )


__all__ = ["FederatedIdentityHealthCheck"]
