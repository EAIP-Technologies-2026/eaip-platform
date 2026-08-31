"""Health check for the job dependency manager."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.jobdep.manager import JobDependencyManager


class JobDepHealthCheck:
    name: str = "jobdep"

    def __init__(self, manager: JobDependencyManager) -> None:
        self._manager = manager

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            graph = self._manager.get_graph()
            details["node_count"] = len(graph.nodes)
            details["dependency_count"] = len(graph.dependencies)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Job dependency manager unavailable: {exc}",
                details={"error": str(exc)},
            )

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Job dependency manager healthy",
            details=details,
        )


__all__ = ["JobDepHealthCheck"]
