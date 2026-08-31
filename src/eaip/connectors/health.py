"""Health check for the connector management subsystem."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class ConnectorHealthCheck:
    """Health check for the connector management subsystem."""

    name: str = "connectors"

    def __init__(self, connector_count: int = 0) -> None:
        """Initialize the health check."""
        self._connector_count = connector_count

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {"connector_count": self._connector_count}
        if self._connector_count > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._connector_count} connector(s) registered",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="No connectors registered",
            details=details,
        )


__all__ = ["ConnectorHealthCheck"]
