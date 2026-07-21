"""Runtime module integration for the retry orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.retry_orchestration.health import RetryOrchestrationHealthCheck
from eaip.retry_orchestration.models import RetryOrchestrationConfig
from eaip.retry_orchestration.service import RetryOrchestrationService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class RetryOrchestrationRuntimeModule:
    name: str = "retry_orchestration"

    def __init__(
        self,
        config: RetryOrchestrationConfig | None = None,
        service: RetryOrchestrationService | None = None,
    ) -> None:
        self._config = config or RetryOrchestrationConfig()
        self._service = service or RetryOrchestrationService(config=self._config)
        self._log = get_logger("eaip.retry_orchestration.integration")

    @property
    def service(self) -> RetryOrchestrationService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("retry_orchestration.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.retry_orchestration",
            title="Retry Orchestration",
            description="Retry policy management, strategy execution, circuit breaker, metrics",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("retry", "orchestration", "circuit_breaker", "policy", "resilience"),
        )
        platform.capabilities.register(capability)
        platform.health.register(RetryOrchestrationHealthCheck(service=self._service))
        self._log.info("retry_orchestration.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("retry_orchestration.module.stopping")


__all__ = ["RetryOrchestrationRuntimeModule"]
