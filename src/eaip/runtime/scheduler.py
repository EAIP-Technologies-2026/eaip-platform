"""Runtime Scheduler — task scheduling and recurring job management.

The :class:`SchedulerModule` is a :class:`~eaip.runtime.module.BaseRuntimeModule`
that manages scheduled and recurring tasks.  It integrates with the runtime
lifecycle via ``on_start`` / ``on_stop`` and exposes health checks.

Design
------
* Jobs are async callables registered with a name and optional schedule.
* Recurring jobs use a simple interval-based schedule (``Duration``).
* The scheduler runs an internal loop that checks for due jobs.
* Cancellation is cooperative: the loop checks a shutdown event.

Usage::

    async def my_task(ctx: RuntimeContext) -> None:
        ...

    scheduler = SchedulerModule()
    scheduler.register("my-job", my_task, interval=Duration.from_seconds(60))

    host.add_module(scheduler)
    async with host:
        ...
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from eaip.exceptions.domain import DuplicateRegistrationError, SchedulerError
from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.runtime.module import BaseRuntimeModule
from eaip.shared.time import Duration, utc_now

if TYPE_CHECKING:
    from datetime import datetime

    from eaip.runtime.context import RuntimeContext
    from eaip.runtime.host import RuntimeHost

JobFn = Callable[..., Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ScheduledJob:
    """Immutable metadata for a registered job.

    Attributes
    ----------
    name:
        Unique job name.
    fn:
        The async callable to invoke.
    interval:
        How often the job should run (``None`` for one-shot).
    last_run:
        Timestamp of the most recent execution, or ``None``.
    running:
        Whether the job is currently executing.
    error_count:
        How many consecutive failures have occurred.
    """

    name: str
    fn: JobFn
    interval: Duration | None = None
    last_run: datetime | None = None
    running: bool = False
    error_count: int = 0

    @property
    def is_recurring(self) -> bool:
        return self.interval is not None

    def is_due(self, now: datetime | None = None) -> bool:
        if self.interval is None:
            return self.last_run is None
        if self.last_run is None:
            return True
        check = now or utc_now()
        return (check - self.last_run) >= self.interval.to_timedelta()


class SchedulerModule(BaseRuntimeModule):
    """Runtime module that manages scheduled and recurring jobs.

    Usage::

        scheduler = SchedulerModule()
        scheduler.register("heartbeat", heartbeat_fn, interval=Duration.from_seconds(30))
        scheduler.register("init", init_fn)  # runs once on start

        host.add_module(scheduler)
        await host.start()
    """

    module_name = "eaip.runtime.scheduler"
    module_dependencies: tuple[str, ...] = ()

    def __init__(self, poll_interval: Duration = Duration.from_seconds(1)) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._poll_interval = poll_interval
        self._shutdown = asyncio.Event()
        self._loop_task: asyncio.Task[None] | None = None
        self._log = get_logger("eaip.runtime.scheduler")
        self._health_status: str = "created"

    # ------------------------------------------------------------------
    # Job registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        fn: JobFn,
        *,
        interval: Duration | None = None,
    ) -> None:
        """Register a job.

        Args:
            name:
                Unique job name.
            fn:
                Async callable to invoke.  Receives ``(self, ctx)`` where
                *self* is this module and *ctx* is the current
                :class:`~eaip.runtime.context.RuntimeContext`.
            interval:
                How often to run.  ``None`` means one-shot (runs once on start).
        """
        if not name:
            raise ValueError("job name must be non-empty")
        if name in self._jobs:
            raise DuplicateRegistrationError(
                f"job {name!r} is already registered",
                context={"job": name},
            )
        self._jobs[name] = ScheduledJob(name=name, fn=fn, interval=interval)
        self._log.info("scheduler.job.registered", job=name, recurring=interval is not None)

    def unregister(self, name: str) -> bool:
        """Remove a job.  Returns ``True`` if it existed."""
        removed = self._jobs.pop(name, None) is not None
        if removed:
            self._log.info("scheduler.job.unregistered", job=name)
        return removed

    def get_job(self, name: str) -> ScheduledJob | None:
        return self._jobs.get(name)

    @property
    def job_names(self) -> list[str]:
        return sorted(self._jobs)

    @property
    def job_count(self) -> int:
        return len(self._jobs)

    # ------------------------------------------------------------------
    # Lifecycle — RuntimeModule protocol
    # ------------------------------------------------------------------

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Start the scheduler loop and run one-shot jobs."""
        self._health_status = "starting"
        self._shutdown.clear()

        # Run one-shot jobs (those without interval) immediately.
        for name, job in list(self._jobs.items()):
            if job.interval is None:
                await self._execute_job(name, ctx)

        # Start the recurring job loop.
        if any(j.interval is not None for j in self._jobs.values()):
            self._loop_task = asyncio.create_task(
                self._run_loop(ctx),
                name="eaip-scheduler-loop",
            )
            self._log.info("scheduler.loop.started")
        else:
            self._log.info("scheduler.no_recurring_jobs")

        self._health_status = "running"

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Signal shutdown and await the scheduler loop."""
        self._health_status = "stopping"
        self._shutdown.set()

        if self._loop_task is not None and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None

        self._health_status = "stopped"
        self._log.info("scheduler.loop.stopped")

    async def check_health(self) -> HealthReport:
        """Report scheduler health based on loop status and job error counts."""
        unhealthy_jobs = [
            name for name, job in self._jobs.items()
            if job.error_count > 0
        ]
        status = HealthStatus.HEALTHY
        message = "scheduler running"
        if not unhealthy_jobs and self._health_status == "running":
            status = HealthStatus.HEALTHY
            message = "scheduler healthy"
        elif unhealthy_jobs:
            status = HealthStatus.DEGRADED
            message = f"scheduler degraded: {len(unhealthy_jobs)} job(s) with errors"
        elif self._health_status == "stopped":
            status = HealthStatus.HEALTHY
            message = "scheduler stopped"
        else:
            status = HealthStatus.DEGRADED
            message = f"scheduler status: {self._health_status}"

        return HealthReport(
            component=self.name,
            status=status,
            message=message,
            details={
                "job_count": len(self._jobs),
                "unhealthy_jobs": unhealthy_jobs,
            },
            observed_at=utc_now(),
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _run_loop(self, ctx: RuntimeContext) -> None:
        """Main scheduler loop — poll for due jobs and execute them."""
        while not self._shutdown.is_set():
            try:
                await self._tick(ctx)
            except asyncio.CancelledError:
                break
            except BaseException as exc:
                self._log.error(
                    "scheduler.loop.error",
                    error=repr(exc),
                )
            await asyncio.sleep(self._poll_interval.seconds)

    async def _tick(self, ctx: RuntimeContext) -> None:
        """Check and execute all due jobs."""
        now = utc_now()
        for name, job in list(self._jobs.items()):
            if not job.is_recurring:
                continue
            if job.running:
                continue
            if not job.is_due(now):
                continue
            asyncio.ensure_future(self._execute_job(name, ctx))

    async def _execute_job(self, name: str, ctx: RuntimeContext) -> None:
        """Execute a single job, recording results."""
        job = self._jobs.get(name)
        if job is None:
            return

        self._jobs[name] = ScheduledJob(
            name=job.name,
            fn=job.fn,
            interval=job.interval,
            last_run=job.last_run,
            running=True,
            error_count=job.error_count,
        )

        self._log.info("scheduler.job.starting", job=name)
        try:
            result = job.fn(self, ctx)
            if inspect.isawaitable(result):
                await result
            self._jobs[name] = ScheduledJob(
                name=job.name,
                fn=job.fn,
                interval=job.interval,
                last_run=utc_now(),
                running=False,
                error_count=0,
            )
            self._log.info("scheduler.job.completed", job=name)
        except BaseException as exc:
            self._log.error(
                "scheduler.job.failed",
                job=name,
                error=repr(exc),
            )
            self._jobs[name] = ScheduledJob(
                name=job.name,
                fn=job.fn,
                interval=job.interval,
                last_run=job.last_run,
                running=False,
                error_count=job.error_count + 1,
            )


__all__ = ["JobFn", "ScheduledJob", "SchedulerModule"]
