"""Health check for form builder service."""

from __future__ import annotations

from eaip.formbuilder.builder import FormBuilderService
from eaip.health.checks import HealthReport, HealthStatus


class FormBuilderHealthCheck:
    name: str = "formbuilder"

    def __init__(self, service: FormBuilderService) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            forms = await self._service.list_forms()
            details["form_count"] = len(forms)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Form builder unavailable: {exc}",
                details={"error": str(exc)},
            )

        published = sum(1 for f in forms if f.status.value == "published")
        details["published_forms"] = published

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if published == 0 and len(forms) > 0:
            status = HealthStatus.DEGRADED
            messages.append("No published forms")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Form builder healthy",
            details=details,
        )


__all__ = ["FormBuilderHealthCheck"]
