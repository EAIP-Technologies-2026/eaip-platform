"""Health check for image tag manager."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ImageTagManagerHealthCheck:
    """Health check for the image tag manager service."""

    name: str = "imgtag"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Image tag manager service healthy",
        )


__all__ = ["ImageTagManagerHealthCheck"]
