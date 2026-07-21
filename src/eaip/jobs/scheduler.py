"""JobScheduler — cron-based and interval-based job scheduling."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eaip.jobs.events import JobScheduled
from eaip.jobs.exceptions import JobNotFoundError
from eaip.jobs.executor import LongRunningJob, LongRunningJobExecutor
from eaip.jobs.models import (
    JobDefinition,
    JobHandler,
    JobRun,
    JobSchedule,
    JobStatus,
)
from eaip.logging.context import get_logger


class JobScheduler:
    """Schedules and manages job execution with cron and interval support."""

    def __init__(
        self,
        executor: LongRunningJobExecutor | None = None,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._executor = executor or LongRunningJobExecutor(event_bus=event_bus, meter=meter)
        self._event_bus = event_bus
        self._meter = meter
        self._definitions: dict[str, JobDefinition] = {}
        self._handlers: dict[str, JobHandler] = {}
        self._scheduled_tasks: dict[str, asyncio.Task[None]] = {}
        self._running = False
        self._log = get_logger("eaip.jobs.scheduler")

    @property
    def executor(self) -> LongRunningJobExecutor:
        return self._executor

    def register_job(
        self,
        definition: JobDefinition,
        handler: JobHandler,
    ) -> str:
        self._definitions[definition.id] = definition
        self._handlers[definition.id] = handler

        lrj = LongRunningJob(
            job_id=definition.id,
            handler=handler,
            timeout_seconds=definition.timeout_seconds,
            retry_config=definition.retry_config,
            event_bus=self._event_bus,
            meter=self._meter,
        )
        self._executor.register_job(lrj)

        if self._event_bus:
            schedule_str = ""
            if definition.schedule:
                if definition.schedule.cron:
                    schedule_str = definition.schedule.cron.to_cron_string()
                elif definition.schedule.interval_seconds:
                    schedule_str = f"every_{definition.schedule.interval_seconds}s"
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(
                        self._event_bus.publish(
                            JobScheduled(
                                job_id=definition.id,
                                job_name=definition.name,
                                schedule=schedule_str,
                                priority=int(definition.priority),
                            )
                        )
                    )
            except RuntimeError:
                pass

        return definition.id

    async def run_once(self, job_id: str) -> JobRun:
        definition = self._definitions.get(job_id)
        if definition is None:
            raise JobNotFoundError(job_id)

        run = JobRun(
            id=uuid.uuid4().hex,
            job_id=job_id,
            job_name=definition.name,
            status=JobStatus.PENDING,
        )
        return await self._executor.execute_job(job_id, run)

    async def start(self) -> None:
        self._running = True
        for defn in self._definitions.values():
            if defn.enabled and defn.schedule:
                task = asyncio.create_task(
                    self._run_scheduled(defn),
                    name=f"jobscheduler:{defn.name}",
                )
                self._scheduled_tasks[defn.id] = task

    async def stop(self) -> None:
        self._running = False
        for task in self._scheduled_tasks.values():
            if not task.done():
                task.cancel()
        if self._scheduled_tasks:
            await asyncio.gather(
                *[t for t in self._scheduled_tasks.values() if not t.done()],
                return_exceptions=True,
            )
        self._scheduled_tasks.clear()

    async def _run_scheduled(self, definition: JobDefinition) -> None:
        schedule = definition.schedule
        if schedule is None:
            return

        max_runs = schedule.max_runs
        run_count = 0

        while self._running and definition.enabled:
            if max_runs > 0 and run_count >= max_runs:
                break

            delay = self._compute_delay(schedule)
            if delay is None:
                await asyncio.sleep(60)
                continue

            await asyncio.sleep(delay)

            run = JobRun(
                id=uuid.uuid4().hex,
                job_id=definition.id,
                job_name=definition.name,
                status=JobStatus.PENDING,
            )
            try:
                await self._executor.execute_job(definition.id, run)
            except Exception as exc:
                self._log.error(
                    "scheduler.job_failed",
                    job_id=definition.id,
                    error=str(exc),
                )
            run_count += 1

            if schedule.interval_seconds is None and schedule.cron:
                await asyncio.sleep(60)

    def _compute_delay(self, schedule: JobSchedule) -> float | None:
        if schedule.interval_seconds and schedule.interval_seconds > 0:
            return schedule.interval_seconds
        if schedule.cron:
            return 1.0
        return None

    def get_definition(self, job_id: str) -> JobDefinition | None:
        return self._definitions.get(job_id)

    def list_definitions(self) -> list[JobDefinition]:
        return list(self._definitions.values())

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._definitions:
            del self._definitions[job_id]
            self._handlers.pop(job_id, None)
            task = self._scheduled_tasks.pop(job_id, None)
            if task and not task.done():
                task.cancel()
            return True
        return False


__all__ = ["JobScheduler"]
