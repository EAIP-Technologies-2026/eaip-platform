"""Runtime module integration for the CI service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.ciservice.health import CIHealthCheck
from eaip.ciservice.models import CIConfig
from eaip.ciservice.service import CIService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CIRuntimeModule:
    name: str = "ciservice"

    def __init__(
        self,
        config: CIConfig | None = None,
        service: CIService | None = None,
    ) -> None:
        self._config = config or CIConfig()
        self._service = service or CIService()
        self._log = get_logger("eaip.ciservice.integration")

    @property
    def service(self) -> CIService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("ciservice.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.ciservice",
            title="Continuous Integration Service",
            description="Pipeline management, build execution, artifact storage, and CI workflow orchestration",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("ciservice", "ci", "pipeline", "build", "artifact"),
        )
        platform.capabilities.register(capability)
        platform.health.register(CIHealthCheck())
        self._log.info("ciservice.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("ciservice.module.stopping")


__all__ = ["CIRuntimeModule"]
