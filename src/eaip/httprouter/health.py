"""Health check for HTTP request router."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class HTTPRouterHealthCheck:
    name: str = "httprouter"

    async def check(self) -> HealthReport:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="HTTP request router healthy",
        )


__all__ = ["HTTPRouterHealthCheck"]
