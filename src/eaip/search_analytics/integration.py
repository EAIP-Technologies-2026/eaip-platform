"""Integration layer — SearchAnalyticsRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger
from eaip.search_analytics.health import SearchAnalyticsHealthCheck
from eaip.search_analytics.service import SearchAnalyticsService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SearchAnalyticsRuntimeModule:
    """RuntimeModule that bootstraps the Search Analytics subsystem.

    Registers health checks, capabilities, and exposes the analytics
    service to other components.
    """

    name: str = "search_analytics"

    def __init__(
        self,
        service: SearchAnalyticsService | None = None,
    ) -> None:
        self._service = service or SearchAnalyticsService()
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.search_analytics.integration")

    @property
    def service(self) -> SearchAnalyticsService:
        return self._service

    @property
    def startup_duration(self) -> float:
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        t0 = time.monotonic()
        self._log.info("search_analytics.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())
            kernel.platform.capabilities.register(self._capability())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "search_analytics.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, kernel: RuntimeKernel | None = None) -> None:  # noqa: ARG002
        self._log.info("search_analytics.integration.stop")
        self._started = False

    async def register_with_runtime(self) -> None:
        self._log.info("search_analytics.integration.register")

    def _health_check(self) -> HealthCheck:
        return SearchAnalyticsHealthCheck()

    def _capability(self) -> Capability:
        return Capability(
            name="search_analytics:service",
            title="Search Analytics Service",
            status=CapabilityStatus.ENABLED,
        )


__all__ = ["SearchAnalyticsRuntimeModule"]
