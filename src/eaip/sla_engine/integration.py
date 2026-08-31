"""RuntimeKernel integration — registers SlaService as a RuntimeModule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.sla_engine.health import SlaHealthCheck
from eaip.sla_engine.service import SlaService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SlaRuntimeModule:
    name: str = "sla_engine"

    def __init__(self, service: SlaService | None = None) -> None:
        self._service = service or SlaService()
        self._log = get_logger("eaip.sla_engine.integration")

    @property
    def service(self) -> SlaService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("sla_engine.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.sla_engine",
            title="SLA Engine",
            description="SLA definition, monitoring, violation detection, and breach escalation",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("sla", "monitoring", "violation", "breach", "alerting"),
        )
        platform.capabilities.register(capability)
        platform.health.register(SlaHealthCheck(service=self._service))
        self._log.info("sla_engine.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("sla_engine.module.stopping")


__all__ = ["SlaRuntimeModule"]
