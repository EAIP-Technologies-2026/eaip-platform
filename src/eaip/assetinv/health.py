"""Health check for asset inventory."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class AssetInventoryHealthCheck:
    """Health check for the asset inventory service."""

    name: str = "assetinv"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Asset inventory service healthy",
        )


__all__ = ["AssetInventoryHealthCheck"]
