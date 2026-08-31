"""Status page service — CRUD, rendering, publishing."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.health.checks import HealthStatus
from eaip.healthagg.events import StatusPageCreated, StatusPageUpdated
from eaip.healthagg.exceptions import StatusPageNotFoundError
from eaip.healthagg.models import HealthStatusPage
from eaip.logging.context import get_logger


class StatusPageService:
    def __init__(self, aggregator: Any | None = None, event_bus: Any | None = None) -> None:
        self._pages: dict[str, HealthStatusPage] = {}
        self._aggregator = aggregator
        self._event_bus = event_bus
        self._log = get_logger("eaip.healthagg.status_page")

    def create_page(
        self,
        name: str,
        description: str = "",
        components: tuple[str, ...] = (),
        layout: dict[str, Any] | None = None,
        refresh_interval_seconds: int = 30,
        public: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> HealthStatusPage:
        page_id = str(uuid.uuid4())
        page = HealthStatusPage(
            id=page_id,
            name=name,
            description=description,
            components=components,
            layout=layout or {},
            refresh_interval_seconds=refresh_interval_seconds,
            public=public,
            metadata=metadata or {},
        )
        self._pages[page_id] = page
        self._publish_event(StatusPageCreated(page_id=page_id, page_name=name))
        return page

    def get_page(self, page_id: str) -> HealthStatusPage:
        page = self._pages.get(page_id)
        if page is None:
            raise StatusPageNotFoundError(
                f"status page {page_id!r} not found",
                context={"page_id": page_id},
            )
        return page

    def update_page(self, page_id: str, **updates: Any) -> HealthStatusPage:
        existing = self.get_page(page_id)
        updated = existing.model_copy(update=updates)
        self._pages[page_id] = updated
        self._publish_event(StatusPageUpdated(page_id=page_id, page_name=updated.name))
        return updated

    def delete_page(self, page_id: str) -> bool:
        return self._pages.pop(page_id, None) is not None

    def list_pages(self) -> list[HealthStatusPage]:
        return list(self._pages.values())

    async def render_page(self, page_id: str) -> dict[str, Any]:
        page = self.get_page(page_id)
        component_statuses: dict[str, str] = {}
        if self._aggregator is not None:
            all_statuses = await self._aggregator.get_all_components()
            for comp in page.components:
                status = all_statuses.get(comp, HealthStatus.UNHEALTHY)
                component_statuses[comp] = status.value
        return {
            "page": page.model_dump(),
            "component_statuses": component_statuses,
            "overall_status": (await self.get_page_status(page_id)).value,
        }

    async def get_page_status(self, page_id: str) -> HealthStatus:
        page = self.get_page(page_id)
        if self._aggregator is None:
            return HealthStatus.HEALTHY
        all_statuses = await self._aggregator.get_all_components()
        statuses = [all_statuses.get(c, HealthStatus.UNHEALTHY) for c in page.components]
        return max(statuses, key=lambda s: s.numeric) if statuses else HealthStatus.HEALTHY

    async def publish_page(self, page_id: str) -> str:
        page = self.get_page(page_id)
        url_stub = f"/status/{page.name.lower().replace(' ', '-')}"
        self._pages[page_id] = page.model_copy(update={"public": True})
        return url_stub

    def set_public_access(self, page_id: str, enabled: bool) -> HealthStatusPage:
        return self.update_page(page_id, public=enabled)

    def _publish_event(self, event: Any) -> None:
        if self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except BaseException:
                self._log.warning(
                    "healthagg.status_page.event_failed", event_type=type(event).__name__
                )


__all__ = ["StatusPageService"]
