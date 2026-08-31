"""Health check for the workflow designer."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.wfdesigner.designer import WorkflowDesigner


class DesignerHealthCheck:
    name: str = "wfdesigner"

    def __init__(self, service: WorkflowDesigner) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            blueprints = await self._service.list_blueprints()
            details["blueprint_count"] = len(blueprints)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Workflow designer unavailable: {exc}",
                details={"error": str(exc)},
            )

        published = sum(1 for b in blueprints if b.status.value == "published")
        details["published_blueprints"] = published

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if published == 0 and len(blueprints) > 0:
            status = HealthStatus.DEGRADED
            messages.append("No published blueprints")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Workflow designer healthy",
            details=details,
        )


__all__ = ["DesignerHealthCheck"]
