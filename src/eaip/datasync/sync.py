"""DataSyncService — create, execute, and monitor sync jobs."""

from __future__ import annotations

from eaip.datasync.events import SyncCompleted, SyncFailed, SyncJobCreated, SyncStarted
from eaip.datasync.exceptions import SyncJobNotFoundError
from eaip.datasync.models import SyncConfig, SyncJob, SyncRun, SyncStatus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DataSyncService:
    """Central service for managing data synchronization jobs and runs."""

    def __init__(self, config: SyncConfig | None = None) -> None:
        self._config = config or SyncConfig()
        self._jobs: dict[str, SyncJob] = {}
        self._runs: dict[str, SyncRun] = {}
        self._log = get_logger("eaip.datasync.service")

    @property
    def config(self) -> SyncConfig:
        return self._config

    async def create_job(self, job: SyncJob) -> SyncJob:
        """Create a new sync job."""
        self._jobs[job.id] = job
        SyncJobCreated(
            job_id=job.id,
            name=job.name,
            sync_type=job.sync_type,
        )
        self._log.info("datasync.job.created", job_id=job.id, name=job.name)
        return job

    async def get_job(self, job_id: str) -> SyncJob:
        """Get a sync job by ID."""
        job = self._jobs.get(job_id)
        if job is None:
            raise SyncJobNotFoundError(f"Sync job not found: {job_id}")
        return job

    async def list_jobs(self) -> list[SyncJob]:
        """List all sync jobs."""
        return list(self._jobs.values())

    async def update_job(self, job_id: str, **changes: object) -> SyncJob:
        """Update an existing sync job."""
        job = self._jobs.get(job_id)
        if job is None:
            raise SyncJobNotFoundError(f"Sync job not found: {job_id}")
        updated = job.model_copy(update={"updated_at": utc_now(), **changes})
        self._jobs[job_id] = updated
        self._log.info("datasync.job.updated", job_id=job_id)
        return updated

    async def delete_job(self, job_id: str) -> None:
        """Delete a sync job."""
        if job_id not in self._jobs:
            raise SyncJobNotFoundError(f"Sync job not found: {job_id}")
        del self._jobs[job_id]
        self._log.info("datasync.job.deleted", job_id=job_id)

    async def start_run(self, run: SyncRun) -> SyncRun:
        """Start a new sync run for a job."""
        job = self._jobs.get(run.job_id)
        if job is None:
            raise SyncJobNotFoundError(f"Sync job not found: {run.job_id}")
        started_run = run.model_copy(update={"status": SyncStatus.RUNNING})
        self._runs[run.id] = started_run
        SyncStarted(run_id=run.id, job_id=run.job_id, started_at=started_run.started_at)
        self._log.info("datasync.run.started", run_id=run.id, job_id=run.job_id)
        return started_run

    async def complete_run(
        self,
        run_id: str,
        items_synced: int = 0,
        items_failed: int = 0,
    ) -> SyncRun:
        """Mark a sync run as completed."""
        run = self._runs.get(run_id)
        if run is None:
            raise SyncJobNotFoundError(f"Sync run not found: {run_id}")
        now = utc_now()
        delta = (now - run.started_at).total_seconds()
        completed_run = run.model_copy(
            update={
                "status": SyncStatus.COMPLETED,
                "completed_at": now,
                "items_synced": items_synced,
                "items_failed": items_failed,
            }
        )
        self._runs[run_id] = completed_run
        SyncCompleted(
            run_id=run_id,
            job_id=completed_run.job_id,
            items_synced=items_synced,
            items_failed=items_failed,
            duration_seconds=round(delta, 3),
        )
        self._log.info("datasync.run.completed", run_id=run_id, items_synced=items_synced)
        return completed_run

    async def fail_run(self, run_id: str, error_message: str = "") -> SyncRun:
        """Mark a sync run as failed."""
        run = self._runs.get(run_id)
        if run is None:
            raise SyncJobNotFoundError(f"Sync run not found: {run_id}")
        failed_run = run.model_copy(
            update={
                "status": SyncStatus.FAILED,
                "completed_at": utc_now(),
                "error_message": error_message,
            }
        )
        self._runs[run_id] = failed_run
        SyncFailed(
            run_id=run_id,
            job_id=failed_run.job_id,
            error_message=error_message,
        )
        self._log.info("datasync.run.failed", run_id=run_id, error=error_message)
        return failed_run

    async def get_run(self, run_id: str) -> SyncRun:
        """Get a sync run by ID."""
        run = self._runs.get(run_id)
        if run is None:
            raise SyncJobNotFoundError(f"Sync run not found: {run_id}")
        return run

    async def list_runs(self, job_id: str | None = None) -> list[SyncRun]:
        """List sync runs, optionally filtered by job."""
        runs = list(self._runs.values())
        if job_id is not None:
            runs = [r for r in runs if r.job_id == job_id]
        return runs

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about sync jobs and runs."""
        total_jobs = len(self._jobs)
        total_runs = len(self._runs)
        completed = sum(1 for r in self._runs.values() if r.status == SyncStatus.COMPLETED)
        failed = sum(1 for r in self._runs.values() if r.status == SyncStatus.FAILED)
        return {
            "total_jobs": total_jobs,
            "total_runs": total_runs,
            "completed_runs": completed,
            "failed_runs": failed,
        }


__all__ = ["DataSyncService"]
