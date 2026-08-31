"""Runtime module integration for the container orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.container.health import ContainerHealthCheck
from eaip.container.models import ContainerConfig
from eaip.container.orchestrator import ContainerOrchestrator
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ContainerRuntimeModule:
    name: str = "container"

    def __init__(
        self,
        config: ContainerConfig | None = None,
        orchestrator: ContainerOrchestrator | None = None,
    ) -> None:
        self._config = config or ContainerConfig()
        self._orchestrator = orchestrator or ContainerOrchestrator()
        self._log = get_logger("eaip.container.integration")

    @property
    def orchestrator(self) -> ContainerOrchestrator:
        return self._orchestrator

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("container.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.container",
            title="Container Orchestrator Interface",
            description="Container lifecycle management, deployment scaling, and health monitoring",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("container", "orchestrator", "deployment", "scaling"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ContainerHealthCheck())
        self._log.info("container.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("container.module.stopping")


__all__ = ["ContainerRuntimeModule"]
