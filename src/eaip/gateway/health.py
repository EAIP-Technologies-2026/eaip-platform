"""Gateway health check."""

from __future__ import annotations

from eaip.gateway.router import ApiRouter
from eaip.health.checks import HealthReport, HealthStatus


class GatewayHealthCheck:
    """Health check for the gateway component.

    Reports healthy when the router is initialised and has no fatal issues.
    """

    name: str = "gateway"

    def __init__(self, router: ApiRouter) -> None:
        """Initialize the health check with the gateway router."""
        self._router = router

    async def check(self) -> HealthReport:
        """Run the gateway health check.

        Returns:
            A health report describing the gateway status.
        """
        endpoint_count = len(self._router.list_endpoints())
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"Gateway operational with {endpoint_count} registered endpoint(s)",
            details={
                "endpoint_count": endpoint_count,
                "middleware_count": len(self._router.pipeline.middlewares),
            },
        )


__all__ = ["GatewayHealthCheck"]
