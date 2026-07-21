"""Runtime module integration for the compensation runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.compensation.health import CompensationHealthCheck
from eaip.compensation.models import CompensationConfig
from eaip.compensation.service import CompensationService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CompensationRuntimeModule:
    name: str = "compensation"

    def __init__(
        self,
        config: CompensationConfig | None = None,
        service: CompensationService | None = None,
    ) -> None:
        self._config = config or CompensationConfig()
        self._service = service or CompensationService(config=self._config)
        self._log = get_logger("eaip.compensation.integration")

    @property
    def service(self) -> CompensationService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("compensation.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.compensation",
            title="Compensation Workflows",
            description="Compensation-based rollback and recovery for distributed workflows",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("compensation", "rollback", "saga", "workflow", "recovery"),
        )
        platform.capabilities.register(capability)
        platform.health.register(CompensationHealthCheck(service=self._service))
        self._log.info("compensation.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("compensation.module.stopping")


__all__ = ["CompensationRuntimeModule"]
