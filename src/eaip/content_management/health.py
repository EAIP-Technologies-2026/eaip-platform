"""Health check for content management."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ContentManagementHealthCheck(HealthCheck):
    name: str = "eaip.content_management"

    def __init__(
        self,
        item_count: int = 0,
        published_count: int = 0,
        draft_count: int = 0,
        active_workflows: int = 0,
    ) -> None:
        self._item_count = item_count
        self._published_count = published_count
        self._draft_count = draft_count
        self._active_workflows = active_workflows

    async def check(self) -> HealthReport:
        details = {
            "total_items": self._item_count,
            "published": self._published_count,
            "drafts": self._draft_count,
            "active_workflows": self._active_workflows,
        }
        if self._active_workflows > 0:
            return HealthReport(
                component="ContentManagement",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._active_workflows} active workflow(s)",
            )
        return HealthReport(
            component="ContentManagement",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = ["ContentManagementHealthCheck"]
