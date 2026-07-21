"""RuntimeKernel integration — registers Experiment Tracking as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.experiment_tracking.health import ExperimentTrackingHealthCheck
from eaip.experiment_tracking.service import ExperimentTrackingService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ExperimentTrackingRuntimeModule:
    """RuntimeModule that registers the experiment tracking subsystem with the kernel.

    On startup:
      - Creates ExperimentTrackingService.
      - Registers ExperimentTrackingHealthCheck.
      - Registers experiment tracking capabilities.

    On shutdown:
      - Cleans up resources.
    """

    name: str = "experiment_tracking"

    def __init__(
        self,
        service: ExperimentTrackingService | None = None,
    ) -> None:
        self._service = service or ExperimentTrackingService()
        self._health_check = ExperimentTrackingHealthCheck(service=self._service)
        self._log = get_logger("eaip.experiment_tracking.integration")

    @property
    def service(self) -> ExperimentTrackingService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("experiment_tracking.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="experiment_tracking:engine",
                title="Experiment Tracking Engine",
                status=CapabilityStatus.ENABLED,
                tags=("experiment_tracking", "engine"),
            )
        )
        kernel.platform.capabilities.register(
            Capability(
                name="experiment_tracking:analysis",
                title="Experiment Analysis",
                status=CapabilityStatus.ENABLED,
                tags=("experiment_tracking", "analysis"),
            )
        )
        kernel.platform.capabilities.register(
            Capability(
                name="experiment_tracking:reports",
                title="Experiment Reports",
                status=CapabilityStatus.ENABLED,
                tags=("experiment_tracking", "reports"),
            )
        )

        kernel.register_module("experiment_tracking.service", self._service)

        self._log.info(
            "experiment_tracking.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("experiment_tracking.module.stop")


__all__ = ["ExperimentTrackingRuntimeModule"]
