"""Runtime module integration for the execution history subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.execution_history.health import ExecutionHistoryHealthCheck
from eaip.execution_history.models import ExecutionHistoryConfig
from eaip.execution_history.service import ExecutionHistoryService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ExecutionHistoryRuntimeModule:
    name: str = "execution_history"

    def __init__(
        self,
        config: ExecutionHistoryConfig | None = None,
        service: ExecutionHistoryService | None = None,
    ) -> None:
        self._config = config or ExecutionHistoryConfig()
        self._service = service or ExecutionHistoryService(config=self._config)
        self._log = get_logger("eaip.execution_history.integration")

    @property
    def service(self) -> ExecutionHistoryService:
        return self._service

    @property
    def config(self) -> ExecutionHistoryConfig:
        return self._config

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("execution_history.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.execution_history",
            title="Execution History",
            description="Record, query, archive, export, and analyze execution records",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=(
                "execution-history",
                "workflow-tracking",
                "auditing",
                "analytics",
            ),
        )
        platform.capabilities.register(capability)
        platform.health.register(ExecutionHistoryHealthCheck(service=self._service))
        self._log.info("execution_history.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("execution_history.module.stopping")


__all__ = ["ExecutionHistoryRuntimeModule"]
