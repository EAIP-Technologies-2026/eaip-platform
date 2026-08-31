"""Health check for the process designer."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus
from eaip.process_designer.service import ProcessDesignerService


class ProcessDesignerHealthCheck:
    """Health check that reports the status of the process designer service."""

    name: str = "process_designer"

    def __init__(self, service: ProcessDesignerService) -> None:
        """Initialize with a reference to the process designer service."""
        self._service = service

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details: dict[str, object] = {}
        try:
            models = await self._service.list_models()
            details["model_count"] = len(models)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Process designer unavailable: {exc}",
                details={"error": str(exc)},
            )

        published = sum(1 for m in models if m.properties.get("published") is True)
        details["published_models"] = published

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if published == 0 and len(models) > 0:
            status = HealthStatus.DEGRADED
            messages.append("No published process models")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Process designer healthy",
            details=details,
        )


__all__ = ["ProcessDesignerHealthCheck"]
