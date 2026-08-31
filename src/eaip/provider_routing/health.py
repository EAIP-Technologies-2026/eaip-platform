"""Provider routing health check."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthReport, HealthStatus

if TYPE_CHECKING:
    from eaip.provider_routing.service import ProviderRoutingService


class ProviderRoutingHealthCheck:
    """Health check for the provider routing subsystem.

    Reports healthy when the routing service is operational.
    """

    name: str = "provider_routing"

    def __init__(self, service: ProviderRoutingService) -> None:
        """Initialize the health check with the routing service."""
        self._service = service

    async def check(self) -> HealthReport:
        """Run the provider routing health check.

        Returns:
            A health report describing the routing subsystem status.
        """
        status = await self._service.health_check()
        total = status["total_routes"]
        active = status["active_routes"]
        circuit_open = status["circuit_open_count"]

        if circuit_open > 0:
            health_status = HealthStatus.DEGRADED
            message = f"Provider routing degraded: {circuit_open} circuit(s) open"
        elif active == 0 and total > 0:
            health_status = HealthStatus.DEGRADED
            message = "Provider routing degraded: no active routes"
        else:
            health_status = HealthStatus.HEALTHY
            message = "Provider routing operational"

        return HealthReport(
            component=self.name,
            status=health_status,
            message=message,
            details=status,
        )


__all__ = ["ProviderRoutingHealthCheck"]
