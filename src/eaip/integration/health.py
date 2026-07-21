"""Health check for the integration hub."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.integration.hub import IntegrationHub


class IntegrationHealthCheck:
    name: str = "integration"

    def __init__(self, hub: IntegrationHub) -> None:
        self._hub = hub

    async def check(self) -> HealthReport:
        error_details: list[str] = []
        connectors = self._hub.list_connectors()
        routes = self._hub.list_routes()
        enabled_connectors = [c for c in connectors if c.enabled]

        if not connectors:
            error_details.append("No connectors registered")
        if not routes:
            error_details.append("No routes configured")
        if not enabled_connectors:
            error_details.append("No enabled connectors")

        status = HealthStatus.HEALTHY
        if error_details:
            status = HealthStatus.DEGRADED

        return HealthReport(
            component="integration",
            status=status,
            message="; ".join(error_details) if error_details else "Integration hub is operational",
            details={
                "connectors_total": len(connectors),
                "connectors_enabled": len(enabled_connectors),
                "routes_total": len(routes),
            },
        )


__all__ = ["IntegrationHealthCheck"]
