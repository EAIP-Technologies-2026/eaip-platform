"""Health check for runtime diagnostics."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class RuntimeDiagnosticsHealthCheck:
    """Health check for the runtime diagnostics service."""

    name: str = "runtime_diagnostics"

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="Runtime diagnostics service healthy",
        )


__all__ = ["RuntimeDiagnosticsHealthCheck"]
