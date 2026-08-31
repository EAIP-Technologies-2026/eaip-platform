"""Workflow designer runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.wfdesigner.designer import WorkflowDesigner
from eaip.wfdesigner.health import DesignerHealthCheck
from eaip.wfdesigner.models import DesignerConfig

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DesignerRuntimeModule:
    name: str = "wfdesigner"

    def __init__(
        self,
        config: DesignerConfig | None = None,
        service: WorkflowDesigner | None = None,
    ) -> None:
        self._config = config or DesignerConfig()
        self._service = service or WorkflowDesigner(config=self._config)
        self._health_check = DesignerHealthCheck(self._service)
        self._log = get_logger("eaip.wfdesigner.integration")

    @property
    def config(self) -> DesignerConfig:
        return self._config

    @property
    def service(self) -> WorkflowDesigner:
        return self._service

    @property
    def health_check(self) -> DesignerHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("wfdesigner.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.wfdesigner",
            title="Workflow Designer Service",
            description="Interactive workflow blueprint creation, node configuration, and lifecycle management",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("workflow", "designer", "blueprint", "node"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("wfdesigner.service", self._service)
        self._log.info("wfdesigner.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("wfdesigner.module.stopping")


__all__ = ["DesignerRuntimeModule"]
