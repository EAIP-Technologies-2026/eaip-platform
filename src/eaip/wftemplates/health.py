"""Workflow Template Library health check."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class WFTemplatesHealthCheck(HealthCheck):
    name: str = "eaip.wftemplates"

    def __init__(
        self,
        total_templates: int = 0,
        published_templates: int = 0,
        total_categories: int = 0,
    ) -> None:
        self._total_templates = total_templates
        self._published_templates = published_templates
        self._total_categories = total_categories

    async def check(self) -> HealthReport:
        details = {
            "total_templates": self._total_templates,
            "published_templates": self._published_templates,
            "total_categories": self._total_categories,
        }
        if self._total_templates == 0:
            return HealthReport(
                component="WorkflowTemplateLibrary",
                status=HealthStatus.HEALTHY,
                details=details,
                message="no templates registered",
            )
        if self._published_templates == 0:
            return HealthReport(
                component="WorkflowTemplateLibrary",
                status=HealthStatus.DEGRADED,
                details=details,
                message="no published templates available",
            )
        return HealthReport(
            component="WorkflowTemplateLibrary",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["WFTemplatesHealthCheck"]
