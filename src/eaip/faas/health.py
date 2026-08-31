"""Health check for Function as a Service runtime."""

from __future__ import annotations

from eaip.faas.runtime import FaaSRuntime
from eaip.health.checks import HealthReport, HealthStatus


class FaaSHealthCheck:
    name: str = "faas"

    def __init__(self, runtime: FaaSRuntime) -> None:
        self._runtime = runtime

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            functions = await self._runtime.list_functions()
            details["function_count"] = len(functions)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"FaaS runtime unavailable: {exc}",
                details={"error": str(exc)},
            )

        active = sum(1 for f in functions if f.status.value == "active")
        failed = sum(1 for f in functions if f.status.value == "failed")
        details["active_functions"] = active
        details["failed_functions"] = failed

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if failed > 0:
            messages.append(f"{failed} failed function(s)")
            status = HealthStatus.DEGRADED

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "FaaS runtime healthy",
            details=details,
        )


__all__ = ["FaaSHealthCheck"]
