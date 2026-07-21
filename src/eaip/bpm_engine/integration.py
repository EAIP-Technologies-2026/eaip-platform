"""Runtime module integration for the BPM engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.bpm_engine.health import BpmHealthCheck
from eaip.bpm_engine.service import BpmService
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class BpmRuntimeModule:
    name: str = "bpm_engine"

    def __init__(self, service: BpmService | None = None) -> None:
        self._service = service or BpmService()
        self._log = get_logger("eaip.bpm_engine.integration")

    @property
    def service(self) -> BpmService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("bpm_engine.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.bpm_engine",
            title="BPM Engine",
            description="BPMN 2.0 process engine with lifecycle management",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("bpmn", "process", "workflow", "engine", "orchestration"),
        )
        platform.capabilities.register(capability)
        platform.health.register(BpmHealthCheck(service=self._service))
        self._log.info("bpm_engine.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("bpm_engine.module.stopping")


__all__ = ["BpmRuntimeModule"]
