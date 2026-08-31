"""Runtime module integration for long-running workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.long_running.health import LongRunningHealthCheck
from eaip.long_running.models import WorkflowPersistenceConfig
from eaip.long_running.service import LongRunningService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class LongRunningRuntimeModule:
    name: str = "long_running"

    def __init__(
        self,
        persistence_config: WorkflowPersistenceConfig | None = None,
        service: LongRunningService | None = None,
    ) -> None:
        self._config = persistence_config or WorkflowPersistenceConfig()
        self._service = service or LongRunningService(persistence_config=self._config)
        self._log = get_logger("eaip.long_running.integration")

    @property
    def service(self) -> LongRunningService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("long_running.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.long_running",
            title="Long-running Workflows",
            description="Durable workflow execution with checkpoints, recovery, and orchestration",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("long_running", "workflows", "durable", "checkpoint", "recovery"),
        )
        platform.capabilities.register(capability)
        platform.health.register(LongRunningHealthCheck(service=self._service))
        self._log.info("long_running.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("long_running.module.stopping")


__all__ = ["LongRunningRuntimeModule"]
