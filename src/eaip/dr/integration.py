"""Runtime integration — DrRuntimeModule for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.dr.failover import FailoverManager
from eaip.dr.health import DrHealthCheck
from eaip.dr.plans import DrPlanManager
from eaip.dr.testing import DrTestService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DrRuntimeModule:
    """RuntimeModule that registers DR components with the kernel."""

    name: str = "dr"

    def __init__(
        self,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._meter = meter
        self._log = get_logger("eaip.dr.integration")
        self.plan_manager = DrPlanManager(event_bus=event_bus)
        self.failover_manager = FailoverManager(event_bus=event_bus)
        self.test_service = DrTestService(event_bus=event_bus)

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("dr.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.dr",
            title="Disaster Recovery",
            description="DR plans, failover automation, RTO/RPO tracking, and recovery testing",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("dr", "disaster-recovery", "failover", "rto", "rpo"),
        )
        platform.capabilities.register(capability)

        health_check = DrHealthCheck(
            plan_manager=self.plan_manager,
            failover_manager=self.failover_manager,
        )
        platform.health.register(health_check)

        self._log.info("dr.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("dr.module.stopping")


__all__ = ["DrRuntimeModule"]
