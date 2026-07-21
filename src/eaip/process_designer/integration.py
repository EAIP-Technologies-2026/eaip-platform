"""Process designer runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.process_designer.health import ProcessDesignerHealthCheck
from eaip.process_designer.service import ProcessDesignerService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ProcessDesignerRuntimeModule:
    """Runtime module that registers the process designer capability and health check."""

    name: str = "process_designer"

    def __init__(
        self,
        service: ProcessDesignerService | None = None,
    ) -> None:
        """Initialize with an optional pre-configured service instance."""
        self._service = service or ProcessDesignerService()
        self._health_check = ProcessDesignerHealthCheck(self._service)
        self._log = get_logger("eaip.process_designer.integration")

    @property
    def service(self) -> ProcessDesignerService:
        """Return the underlying process designer service instance."""
        return self._service

    @property
    def health_check(self) -> ProcessDesignerHealthCheck:
        """Return the health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the process designer capability and health check with the platform."""
        self._log.info("process_designer.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.process_designer",
            title="Process Designer",
            description="Advanced process model design, validation, simulation, import/export",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("process", "designer", "bpmn", "simulation"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("process_designer.service", self._service)
        self._log.info("process_designer.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Gracefully stop the module."""
        self._log.info("process_designer.module.stopping")


__all__ = ["ProcessDesignerRuntimeModule"]
