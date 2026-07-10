"""RuntimeKernel integration — registers WorkforceRuntime as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.jobs.scheduler import JobScheduler
from eaip.logging.context import get_logger
from eaip.workforce.health import WorkforceHealthCheck
from eaip.workforce.orchestrator import WorkforceOrchestrator
from eaip.workforce.scheduler import WorkforceScheduler
from eaip.workforce.worker import WorkerRegistry

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class WorkforceRuntimeModule:
    """RuntimeModule that registers the workforce subsystem with the kernel.

    On startup:
      - Creates WorkerRegistry, WorkforceOrchestrator, WorkforceScheduler.
      - Registers WorkforceHealthCheck.
      - Registers workforce capability.

    On shutdown:
      - Cleans up schedules and assignments.
    """

    name: str = "workforce"

    def __init__(
        self,
        registry: WorkerRegistry | None = None,
        orchestrator: WorkforceOrchestrator | None = None,
        scheduler: WorkforceScheduler | None = None,
        agent_runtime: Any = None,
        workflow_engine: Any = None,
        job_scheduler: JobScheduler | None = None,
        event_bus: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._registry = registry or WorkerRegistry(event_bus=event_bus)
        self._orchestrator = orchestrator or WorkforceOrchestrator(
            registry=self._registry,
            event_bus=event_bus,
            agent_runtime=agent_runtime,
            workflow_engine=workflow_engine,
            job_scheduler=job_scheduler,
        )
        self._job_scheduler = job_scheduler or JobScheduler(event_bus=event_bus)
        self._scheduler = scheduler or WorkforceScheduler(
            registry=self._registry,
            job_scheduler=self._job_scheduler,
            event_bus=event_bus,
        )
        self._health_check = WorkforceHealthCheck()
        self._log = get_logger("eaip.workforce.integration")

    @property
    def registry(self) -> WorkerRegistry:
        return self._registry

    @property
    def orchestrator(self) -> WorkforceOrchestrator:
        return self._orchestrator

    @property
    def scheduler(self) -> WorkforceScheduler:
        return self._scheduler

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("workforce.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(Capability(
            name="workforce:runtime",
            title="Digital Workforce Runtime",
            status=CapabilityStatus.ENABLED,
            tags=("workforce", "runtime"),
        ))

        kernel.register_module("workforce.registry", self._registry)
        kernel.register_module("workforce.orchestrator", self._orchestrator)
        kernel.register_module("workforce.scheduler", self._scheduler)

        self._log.info(
            "workforce.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("workforce.module.stop")


__all__ = ["WorkforceRuntimeModule"]
