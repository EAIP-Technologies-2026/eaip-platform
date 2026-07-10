"""Runtime integration — JobRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.jobs.executor import LongRunningJobExecutor
from eaip.jobs.health import JobHealthCheck
from eaip.jobs.scheduler import JobScheduler
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class JobRuntimeModule:
    """RuntimeModule that registers the job scheduler with the kernel."""

    name: str = "jobs"

    def __init__(
        self,
        scheduler: JobScheduler | None = None,
        executor: LongRunningJobExecutor | None = None,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._meter = meter
        self._executor = executor or LongRunningJobExecutor(event_bus=event_bus, meter=meter)
        self._scheduler = scheduler or JobScheduler(
            executor=self._executor, event_bus=event_bus, meter=meter,
        )
        self._health_check = JobHealthCheck(
            scheduler=self._scheduler, executor=self._executor,
        )
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.jobs.integration")

    @property
    def scheduler(self) -> JobScheduler:
        return self._scheduler

    @property
    def executor(self) -> LongRunningJobExecutor:
        return self._executor

    @property
    def startup_duration(self) -> float:
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("jobs.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(Capability(
            name="jobs:scheduler",
            title="Job Scheduler",
            status=CapabilityStatus.ENABLED,
            tags=("jobs", "scheduler"),
        ))

        kernel.register_module("job_scheduler", self._scheduler)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "jobs.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("jobs.module.stop")
        await self._scheduler.stop()


__all__ = ["JobRuntimeModule"]
