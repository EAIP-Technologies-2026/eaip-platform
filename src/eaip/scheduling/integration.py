from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.scheduling.repository import ScheduleExecutionRepository, ScheduleRepository
from eaip.scheduling.service import SchedulingService
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

log = get_logger("eaip.scheduling.integration")


class SchedulingHealthCheck(HealthCheck):
    name: str = "eaip.scheduling"

    def __init__(self, service: SchedulingService | None = None) -> None:
        self._service = service

    async def check(self) -> HealthReport:
        try:
            return HealthReport(
                component="SchedulingEngine",
                status=HealthStatus.HEALTHY,
                message="scheduling engine healthy",
                details={"engine": "scheduling"},
            )
        except Exception as exc:
            return HealthReport(
                component="SchedulingEngine",
                status=HealthStatus.UNHEALTHY,
                message=f"scheduling engine unhealthy: {exc}",
            )


class SchedulingModule:
    name: str = "scheduling"

    def __init__(
        self,
        repo: ScheduleRepository | None = None,
        exec_repo: ScheduleExecutionRepository | None = None,
        service: SchedulingService | None = None,
        event_bus: Any | None = None,
        workflow_engine: Any | None = None,
        mission_registry: Any | None = None,
        agent_runtime: Any | None = None,
        tick_interval_seconds: float = 15.0,
    ) -> None:
        self._event_bus = event_bus
        self._repo = repo or ScheduleRepository()
        self._exec_repo = exec_repo or ScheduleExecutionRepository()
        self._service = service or SchedulingService(
            repo=self._repo,
            exec_repo=self._exec_repo,
            event_bus=event_bus,
            workflow_engine=workflow_engine,
            mission_registry=mission_registry,
            agent_runtime=agent_runtime,
        )
        self._tick_interval = tick_interval_seconds
        self._health_check = SchedulingHealthCheck(service=self._service)
        self._log = get_logger("eaip.scheduling.integration")
        self._tick_task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def repo(self) -> ScheduleRepository:
        return self._repo

    @property
    def exec_repo(self) -> ScheduleExecutionRepository:
        return self._exec_repo

    @property
    def service(self) -> SchedulingService:
        return self._service

    @property
    def health_check(self) -> SchedulingHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("scheduling.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="scheduling:engine",
                title="Advanced Scheduling Engine",
                status=CapabilityStatus.ENABLED,
                tags=("scheduling", "engine"),
            )
        )

        kernel.register_module("scheduling.repo", self._repo)
        kernel.register_module("scheduling.exec_repo", self._exec_repo)
        kernel.register_module("scheduling.service", self._service)

        self._running = True
        self._tick_task = asyncio.create_task(self._tick_loop(), name="scheduling:tick")

        try:
            kernel.scheduler.every("scheduling:tick", self._tick_interval, self._tick)
        except Exception:
            pass

        self._log.info("scheduling.module.complete", duration_s=round(time.monotonic() - t0, 3))

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("scheduling.module.stop")
        self._running = False
        if self._tick_task is not None:
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
            self._tick_task = None

    async def _tick(self, *_: Any, **__: Any) -> None:
        try:
            due = await self._service.get_all_due(utc_now())
            for schedule in due:
                try:
                    await self._service.execute(schedule.id, schedule.tenant_id)
                except Exception as exc:
                    self._log.warning(
                        "scheduling.tick.execute_failed",
                        schedule_id=schedule.id,
                        tenant_id=schedule.tenant_id,
                        error=str(exc),
                    )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._log.error("scheduling.tick.failed", error=repr(exc))

    async def _tick_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._tick_interval)
            except asyncio.CancelledError:
                break
            if not self._running:
                break
            await self._tick()


__all__ = ["SchedulingHealthCheck", "SchedulingModule"]
