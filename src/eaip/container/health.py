"""Health check for the container orchestrator."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ContainerHealthCheck:
    name: str = "container"

    def __init__(self, container_count: int = 0, deployment_count: int = 0) -> None:
        self._container_count = container_count
        self._deployment_count = deployment_count

    async def check(self) -> HealthReport:
        details = {
            "container_count": self._container_count,
            "deployment_count": self._deployment_count,
        }
        status = HealthStatus.HEALTHY
        message = "Container orchestrator is operational"

        if self._container_count == 0:
            status = HealthStatus.DEGRADED
            message = "No containers registered"

        return HealthReport(
            component="container",
            status=status,
            message=message,
            details=details,
        )


__all__ = ["ContainerHealthCheck"]
