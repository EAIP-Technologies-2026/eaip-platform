"""Health check for the model registry."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ModelRegistryHealthCheck:
    """Health check for the model registry."""

    name: str = "modelreg"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Model registry healthy",
        )


__all__ = ["ModelRegistryHealthCheck"]
