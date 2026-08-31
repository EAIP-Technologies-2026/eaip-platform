"""BatchJobScheduler — schedule, execute, and monitor batch processing jobs."""

from __future__ import annotations

import uuid

from eaip.batchjob.events import BatchJobCompleted, BatchJobCreated, BatchJobFailed, BatchJobStarted
from eaip.batchjob.exceptions import BatchJobError, BatchJobNotFoundError
from eaip.batchjob.models import BatchJob, BatchJobConfig, BatchJobExecution, BatchJobStatus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class BatchJobScheduler:
    """Central service for scheduling and managing batch jobs."""

    def __init__(self, config: BatchJobConfig | None = None) -> None:
        self._config = config or BatchJobConfig()
        self._jobs: dict[str, BatchJob] = {}
        self._executions: dict[str, BatchJobExecution] = {}
        self._log = get_logger("eaip.batchjob.scheduler")

    @property
    def config(self) -> BatchJobConfig:
        return self._config

    async def create_job(self, job: BatchJob) -> BatchJob:
        """Register a new batch job."""
        self._jobs[job.id] = job
        event = BatchJobCreated(
            job_id=job.id,
            name=job.name,
            job_type=job.job_type,
            parameters=job.parameters,
        )
        self._log.info("batchjob.job.created", job_id=job.id, name=job.name)
        return job

    async def get_job(self, job_id: str) -> BatchJob:
        """Retrieve a batch job by ID."""
        job = self._jobs.get(job_id)
        if job is None:
            raise BatchJobNotFoundError(f"Job '{job_id}' not found")
        return job

    async def list_jobs(self) -> list[BatchJob]:
        """List all registered batch jobs."""
        return list(self._jobs.values())

    async def start_execution(self, job_id: str) -> BatchJobExecution:
        """Start a new execution for the given job."""
        job = await self.get_job(job_id)
        if not job.enabled:
            raise BatchJobError(f"Job '{job_id}' is disabled")
        execution = BatchJobExecution(
            id=f"exec_{uuid.uuid4().hex[:8]}_{job_id}",
            job_id=job_id,
            status=BatchJobStatus.RUNNING,
            started_at=utc_now(),
        )
        self._executions[execution.id] = execution
        event = BatchJobStarted(job_id=job_id, execution_id=execution.id)
        self._log.info("batchjob.execution.started", job_id=job_id, exec_id=execution.id)
        return execution

    async def complete_execution(
        self, execution_id: str, result: dict[str, object] | None = None
    ) -> BatchJobExecution:
        """Mark an execution as completed."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise BatchJobNotFoundError(f"Execution '{execution_id}' not found")
        updated = execution.model_copy(
            update={
                "status": BatchJobStatus.COMPLETED,
                "completed_at": utc_now(),
                "result": result,
            },
            deep=True,
        )
        self._executions[execution_id] = updated
        event = BatchJobCompleted(
            job_id=updated.job_id,
            execution_id=execution_id,
            result=result or {},
        )
        self._log.info("batchjob.execution.completed", exec_id=execution_id)
        return updated

    async def fail_execution(
        self, execution_id: str, error: str, retry_count: int = 0
    ) -> BatchJobExecution:
        """Mark an execution as failed."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise BatchJobNotFoundError(f"Execution '{execution_id}' not found")
        updated = execution.model_copy(
            update={
                "status": BatchJobStatus.FAILED,
                "completed_at": utc_now(),
                "error": error,
            },
            deep=True,
        )
        self._executions[execution_id] = updated
        event = BatchJobFailed(
            job_id=updated.job_id,
            execution_id=execution_id,
            error=error,
            retry_count=retry_count,
        )
        self._log.info("batchjob.execution.failed", exec_id=execution_id, error=error)
        return updated

    async def get_execution(self, execution_id: str) -> BatchJobExecution:
        """Retrieve an execution by ID."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise BatchJobNotFoundError(f"Execution '{execution_id}' not found")
        return execution

    async def list_executions(self, job_id: str | None = None) -> list[BatchJobExecution]:
        """List executions, optionally filtered by job."""
        if job_id is None:
            return list(self._executions.values())
        return [e for e in self._executions.values() if e.job_id == job_id]


__all__ = ["BatchJobScheduler"]
