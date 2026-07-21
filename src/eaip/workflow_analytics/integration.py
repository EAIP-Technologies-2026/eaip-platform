"""RuntimeKernel integration — registers WorkflowAnalytics as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.workflow_analytics.health import WorkflowAnalyticsHealthCheck
from eaip.workflow_analytics.service import WorkflowAnalyticsService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class WorkflowAnalyticsRuntimeModule:
    """RuntimeModule that registers the workflow analytics subsystem with the kernel.

    On startup:
      - Creates WorkflowAnalyticsService.
      - Registers WorkflowAnalyticsHealthCheck.
      - Registers workflow analytics capabilities.

    On shutdown:
      - Cleans up resources.
    """

    name: str = "workflow_analytics"

    def __init__(
        self,
        service: WorkflowAnalyticsService | None = None,
    ) -> None:
        self._service = service or WorkflowAnalyticsService()
        self._health_check = WorkflowAnalyticsHealthCheck(service=self._service)
        self._log = get_logger("eaip.workflow_analytics.integration")

    @property
    def service(self) -> WorkflowAnalyticsService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("workflow_analytics.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="workflow_analytics:engine",
                title="Workflow Analytics Engine",
                status=CapabilityStatus.ENABLED,
                tags=("workflow_analytics", "engine"),
            )
        )
        kernel.platform.capabilities.register(
            Capability(
                name="workflow_analytics:reporting",
                title="Workflow Analytics Reporting",
                status=CapabilityStatus.ENABLED,
                tags=("workflow_analytics", "reporting"),
            )
        )

        kernel.register_module("workflow_analytics.service", self._service)

        self._log.info(
            "workflow_analytics.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("workflow_analytics.module.stop")


__all__ = ["WorkflowAnalyticsRuntimeModule"]
