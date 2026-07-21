"""Long-running job executor with progress, checkpointing, and cancellation."""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import suppress
from typing import Any

from eaip.jobs.events import (
    JobCompleted,
    JobFailed,
    JobProgress as JobProgressEvent,
    JobStarted,
)
from eaip.jobs.exceptions import JobNotFoundError
from eaip.jobs.models import JobHandler, JobRun, JobStatus, RetryConfig
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class LongRunningJob:
    """Represents a long-running job with progress tracking and checkpointing."""

    def __init__(
        self,
        job_id: str,
        handler: JobHandler,
        *,
        timeout_seconds: float = 0.0,
        retry_config: RetryConfig | None = None,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._job_id = job_id
        self._handler = handler
        self._timeout = timeout_seconds
        self._retry_config = retry_config
        self._event_bus = event_bus
        self._meter = meter
        self._log = get_logger("eaip.jobs.executor")
        self._runs: dict[str, JobRun] = {}
        self._cancel_flags: set[str] = set()

    async def execute(self, run: JobRun) -> JobRun:
        run_id = run.id or uuid.uuid4().hex
        started_at = time.monotonic()

        run = JobRun(
            **{
                **run.model_dump(),
                "id": run_id,
                "status": JobStatus.RUNNING,
                "started_at": utc_now(),
            }
        )
        self._runs[run_id] = run

        await self._publish(
            JobStarted(
                run_id=run_id,
                job_id=self._job_id,
                job_name=run.job_name,
                attempt=run.attempt,
            )
        )
        self._record_metric("job.started", {"job_id": self._job_id})

        max_attempts = (self._retry_config.max_retries + 1) if self._retry_config else 1
        last_error: str | None = None

        for attempt in range(max_attempts):
            if run_id in self._cancel_flags:
                run = JobRun(**{**run.model_dump(), "status": JobStatus.CANCELLED})
                self._cancel_flags.discard(run_id)
                return run

            if attempt > 0 and self._retry_config:
                backoff = self._retry_config.backoff_multiplier ** (attempt - 1)
                delay = min(
                    self._retry_config.delay_seconds * backoff,
                    self._retry_config.max_delay_seconds,
                )
                await asyncio.sleep(delay)

            try:
                coro = self._handler.execute(run)
                if self._timeout > 0:
                    result = await asyncio.wait_for(coro, timeout=self._timeout)
                else:
                    result = await coro
            except TimeoutError:
                last_error = f"job timed out after {self._timeout}s"
                run = JobRun(**{**run.model_dump(), "attempt": attempt, "error": last_error})
                await self._publish(
                    JobFailed(
                        run_id=run_id,
                        job_id=self._job_id,
                        job_name=run.job_name,
                        attempt=attempt,
                        error=last_error,
                        will_retry=attempt < max_attempts - 1,
                    )
                )
                continue
            except Exception as exc:
                last_error = str(exc)
                run = JobRun(**{**run.model_dump(), "attempt": attempt, "error": last_error})
                will_retry = attempt < max_attempts - 1
                await self._publish(
                    JobFailed(
                        run_id=run_id,
                        job_id=self._job_id,
                        job_name=run.job_name,
                        attempt=attempt,
                        error=last_error,
                        will_retry=will_retry,
                    )
                )
                if not will_retry:
                    break
                continue

            elapsed = (time.monotonic() - started_at) * 1000
            run = JobRun(
                **{
                    **run.model_dump(),
                    "status": JobStatus.COMPLETED,
                    "result": result,
                    "duration_ms": elapsed,
                    "completed_at": utc_now(),
                }
            )
            self._runs[run_id] = run
            await self._publish(
                JobCompleted(
                    run_id=run_id,
                    job_id=self._job_id,
                    job_name=run.job_name,
                    attempt=attempt,
                    duration_ms=elapsed,
                    result=result,
                )
            )
            self._record_metric("job.completed", {"job_id": self._job_id})
            return run

        elapsed = (time.monotonic() - started_at) * 1000
        run = JobRun(
            **{
                **run.model_dump(),
                "status": JobStatus.FAILED,
                "error": last_error or "unknown error",
                "duration_ms": elapsed,
                "completed_at": utc_now(),
            }
        )
        self._runs[run_id] = run
        await self._publish(
            JobFailed(
                run_id=run_id,
                job_id=self._job_id,
                job_name=run.job_name,
                attempt=max_attempts - 1,
                error=last_error or "unknown error",
                will_retry=False,
            )
        )
        self._record_metric("job.failed", {"job_id": self._job_id})
        return run

    async def report_progress(self, run_id: str, progress: float, message: str = "") -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        run = JobRun(
            **{
                **run.model_dump(),
                "progress": progress,
                "progress_message": message,
            }
        )
        self._runs[run_id] = run
        await self._publish(
            JobProgressEvent(
                run_id=run_id,
                job_id=self._job_id,
                job_name=run.job_name,
                progress=progress,
                message=message,
            )
        )

    async def save_checkpoint(self, run_id: str, data: dict[str, Any]) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        run = JobRun(**{**run.model_dump(), "checkpoint_data": data})
        self._runs[run_id] = run

    async def cancel(self, run_id: str) -> None:
        self._cancel_flags.add(run_id)
        run = self._runs.get(run_id)
        if run and run.status in (JobStatus.PENDING, JobStatus.RUNNING):
            await self._handler.cancel(run_id)

    def get_run(self, run_id: str) -> JobRun | None:
        return self._runs.get(run_id)

    def list_runs(self, limit: int = 100) -> list[JobRun]:
        runs = list(self._runs.values())
        runs.sort(key=lambda r: r.created_at, reverse=True)
        return runs[:limit]

    async def _publish(self, event: Any) -> None:
        if self._event_bus:
            try:
                await self._event_bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)

    def _record_metric(self, name: str, labels: dict[str, str]) -> None:
        if self._meter:
            with suppress(Exception):
                self._meter.counter(f"job.{name}", labels=labels).inc()


class LongRunningJobExecutor:
    """High-level executor that manages multiple long-running jobs."""

    def __init__(
        self,
        event_bus: Any = None,
        meter: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._meter = meter
        self._jobs: dict[str, LongRunningJob] = {}

    def register_job(self, job: LongRunningJob) -> None:
        self._jobs[job._job_id] = job

    def get_job(self, job_id: str) -> LongRunningJob | None:
        return self._jobs.get(job_id)

    async def execute_job(self, job_id: str, run: JobRun) -> JobRun:
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return await job.execute(run)

    async def cancel_job(self, job_id: str, run_id: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            await job.cancel(run_id)

    def get_run(self, job_id: str, run_id: str) -> JobRun | None:
        job = self._jobs.get(job_id)
        if job:
            return job.get_run(run_id)
        return None


__all__ = [
    "LongRunningJob",
    "LongRunningJobExecutor",
]
