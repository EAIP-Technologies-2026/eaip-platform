"""Health check for deployment & release management."""

from __future__ import annotations

from typing import Any

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class DeployHealthCheck(HealthCheck):
    """Health check for the deployment & release management subsystem."""

    name: str = "eaip.deploy"

    def __init__(
        self,
        environments: dict[str, dict[str, Any]] | None = None,
        last_deployment_status: str = "",
    ) -> None:
        """Initialize the health check with environment and deployment status."""
        self._environments = environments or {}
        self._last_deployment_status = last_deployment_status

    async def check(self) -> HealthReport:
        """Run the deployment health check.

        Returns:
            UNHEALTHY if the last deployment failed, HEALTHY otherwise.
        """
        details: dict[str, Any] = {
            "environments": self._environments,
            "last_deployment_status": self._last_deployment_status,
        }
        if self._last_deployment_status == "failed":
            return HealthReport(
                component="DeployManager",
                status=HealthStatus.UNHEALTHY,
                details=details,
                message="last deployment failed",
            )
        return HealthReport(
            component="DeployManager",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["DeployHealthCheck"]
