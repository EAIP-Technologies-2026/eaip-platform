"""Health check for the cross-platform connector bridge."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class XBridgeHealthCheck:
    """Health check for the cross-platform connector bridge."""

    name: str = "xbridge"

    def __init__(self, connector_count: int = 0, route_count: int = 0) -> None:
        self._connector_count = connector_count
        self._route_count = route_count

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "connector_count": self._connector_count,
            "route_count": self._route_count,
        }
        if self._connector_count > 0 and self._route_count > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._connector_count} connector(s), {self._route_count} route(s)",
                details=details,
            )
        if self._connector_count == 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="No connectors registered",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="No bridge routes configured",
            details=details,
        )


__all__ = ["XBridgeHealthCheck"]
