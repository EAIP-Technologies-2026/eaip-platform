"""RuntimeKernel integration — registers WorkflowTemplateRegistry as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.wftemplates.health import WFTemplatesHealthCheck
from eaip.wftemplates.importer import WorkflowTemplateImporter
from eaip.wftemplates.registry import WorkflowTemplateRegistry

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class WFTemplatesRuntimeModule:
    name: str = "wftemplates"

    def __init__(
        self,
        registry: WorkflowTemplateRegistry | None = None,
        importer: WorkflowTemplateImporter | None = None,
        event_bus: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._registry = registry or WorkflowTemplateRegistry(event_bus=event_bus)
        self._importer = importer or WorkflowTemplateImporter(
            registry=self._registry, event_bus=event_bus
        )
        self._health_check = WFTemplatesHealthCheck()
        self._log = get_logger("eaip.wftemplates.integration")

    @property
    def registry(self) -> WorkflowTemplateRegistry:
        return self._registry

    @property
    def importer(self) -> WorkflowTemplateImporter:
        return self._importer

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("wftemplates.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="wftemplates:library",
                title="Workflow Template Library",
                status=CapabilityStatus.ENABLED,
                tags=("workflow", "templates", "library"),
            )
        )

        kernel.register_module("wftemplates.registry", self._registry)
        kernel.register_module("wftemplates.importer", self._importer)

        self._log.info(
            "wftemplates.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("wftemplates.module.stop")


__all__ = ["WFTemplatesRuntimeModule"]
