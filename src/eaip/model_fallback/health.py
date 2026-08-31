"""Health check for the model fallback subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthReport, HealthStatus

if TYPE_CHECKING:
    from eaip.model_fallback.service import ModelFallbackService


class ModelFallbackHealthCheck:
    """Health check for the model fallback service."""

    name: str = "eaip.model_fallback"

    def __init__(self, service: ModelFallbackService) -> None:
        """Initialize the health check with a reference to the fallback service."""
        self._service = service

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        config = self._service.config
        metrics = await self._service.get_all_metrics()
        chains = config.chains

        total_executions = sum(m.total_executions for m in metrics.values())
        failed_executions = sum(m.failed_executions for m in metrics.values())
        degraded_executions = sum(m.degraded_executions for m in metrics.values())

        details: dict[str, object] = {
            "chains": len(chains),
            "total_executions": total_executions,
            "failed_executions": failed_executions,
            "degraded_executions": degraded_executions,
        }

        if failed_executions > total_executions * 0.5 and total_executions > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message="High fallback failure rate detected",
                details=details,
            )

        if degraded_executions > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message=f"{degraded_executions} degraded execution(s)",
                details=details,
            )

        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message=f"{len(chains)} chain(s), {total_executions} execution(s)",
            details=details,
        )


__all__ = ["ModelFallbackHealthCheck"]
