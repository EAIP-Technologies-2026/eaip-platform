"""RuntimeKernel integration — registers AiAnalytics as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.ai_analytics.health import AiAnalyticsHealthCheck
from eaip.ai_analytics.service import AiAnalyticsService
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AiAnalyticsRuntimeModule:
    """RuntimeModule that registers the AI analytics subsystem with the kernel.

    On startup:
      - Creates AiAnalyticsService.
      - Registers AiAnalyticsHealthCheck.
      - Registers AI analytics capabilities.

    On shutdown:
      - Cleans up resources.
    """

    name: str = "ai_analytics"

    def __init__(
        self,
        service: AiAnalyticsService | None = None,
    ) -> None:
        self._service = service or AiAnalyticsService()
        self._health_check = AiAnalyticsHealthCheck(service=self._service)
        self._log = get_logger("eaip.ai_analytics.integration")

    @property
    def service(self) -> AiAnalyticsService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("ai_analytics.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="ai_analytics:engine",
                title="AI Analytics Engine",
                status=CapabilityStatus.ENABLED,
                tags=("ai", "analytics", "engine"),
            )
        )
        kernel.platform.capabilities.register(
            Capability(
                name="ai_analytics:dashboard",
                title="AI Analytics Dashboard",
                status=CapabilityStatus.ENABLED,
                tags=("ai", "analytics", "dashboard"),
            )
        )
        kernel.platform.capabilities.register(
            Capability(
                name="ai_analytics:anomaly",
                title="AI Anomaly Detection",
                status=CapabilityStatus.ENABLED,
                tags=("ai", "analytics", "anomaly"),
            )
        )
        kernel.platform.capabilities.register(
            Capability(
                name="ai_analytics:forecast",
                title="AI Forecast Engine",
                status=CapabilityStatus.ENABLED,
                tags=("ai", "analytics", "forecast"),
            )
        )

        kernel.register_module("ai_analytics.service", self._service)

        self._log.info(
            "ai_analytics.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("ai_analytics.module.stop")


__all__ = ["AiAnalyticsRuntimeModule"]
