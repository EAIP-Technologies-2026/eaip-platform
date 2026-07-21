"""Health check for the content registry."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus


class ContentHealthCheck(HealthCheck):
    name: str = "eaip.content.registry"

    def __init__(
        self,
        item_count: int = 0,
        published_count: int = 0,
        archived_count: int = 0,
        deprecated_count: int = 0,
        draft_count: int = 0,
        active_workflows: int = 0,
    ) -> None:
        self._item_count = item_count
        self._published_count = published_count
        self._archived_count = archived_count
        self._deprecated_count = deprecated_count
        self._draft_count = draft_count
        self._active_workflows = active_workflows

    async def check(self) -> HealthReport:
        details = {
            "total_items": self._item_count,
            "published": self._published_count,
            "archived": self._archived_count,
            "deprecated": self._deprecated_count,
            "drafts": self._draft_count,
            "active_workflows": self._active_workflows,
        }
        if self._active_workflows > 0:
            return HealthReport(
                component="ContentRegistry",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._active_workflows} active publishing workflow(s)",
            )
        if self._deprecated_count > 0:
            return HealthReport(
                component="ContentRegistry",
                status=HealthStatus.DEGRADED,
                details=details,
                message=f"{self._deprecated_count} deprecated content item(s)",
            )
        return HealthReport(
            component="ContentRegistry",
            status=HealthStatus.HEALTHY,
            details=details,
        )


__all__ = [
    "ContentHealthCheck",
]
