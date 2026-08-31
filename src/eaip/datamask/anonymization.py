"""Anonymization service — create and execute anonymization jobs."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.datamask.events import (
    AnonymizationCompleted,
    AnonymizationFailed,
    AnonymizationStarted,
)
from eaip.datamask.exceptions import AnonymizationError
from eaip.datamask.masking import DataMaskingService
from eaip.datamask.models import AnonymizationJob, JobStatus, MaskingRule
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

logger = get_logger("eaip.datamask.anonymization")


class AnonymizationService:
    def __init__(
        self,
        masking_service: DataMaskingService | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._masking_service = masking_service or DataMaskingService()
        self._event_bus = event_bus or EventBus()
        self._jobs: dict[str, AnonymizationJob] = {}

    async def create_job(
        self,
        source: str,
        rules: tuple[MaskingRule, ...],
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AnonymizationJob:
        job_id = str(uuid.uuid4())
        job = AnonymizationJob(
            id=job_id,
            name=name or f"anonymization-{job_id[:8]}",
            source=source,
            rules=rules,
            status=JobStatus.PENDING,
            metadata=metadata or {},
        )
        self._jobs[job.id] = job
        return job

    async def execute_job(self, job_id: str) -> AnonymizationJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise AnonymizationError(f"Job '{job_id}' not found")

        started = utc_now()
        updated = job.model_copy(update={"status": JobStatus.RUNNING, "started_at": started})
        self._jobs[job_id] = updated

        await self._event_bus.publish(
            AnonymizationStarted(
                job_id=updated.id,
                job_name=updated.name,
                source=updated.source,
                rule_count=len(updated.rules),
            )
        )

        try:
            processed, skipped = 0, 0
            for record in self._iter_source(updated.source):
                masked = await self._masking_service.apply_masking(record, updated.rules)
                if masked != record:
                    processed += 1
                else:
                    skipped += 1

            completed_at = utc_now()
            duration = (completed_at - started).total_seconds() * 1000

            finished = updated.model_copy(
                update={
                    "status": JobStatus.COMPLETED,
                    "records_processed": processed,
                    "records_skipped": skipped,
                    "completed_at": completed_at,
                }
            )
            self._jobs[job_id] = finished

            await self._event_bus.publish(
                AnonymizationCompleted(
                    job_id=finished.id,
                    job_name=finished.name,
                    records_processed=processed,
                    records_skipped=skipped,
                    duration_ms=duration,
                )
            )
            return finished

        except Exception as exc:
            failed_at = utc_now()
            failed = updated.model_copy(
                update={
                    "status": JobStatus.FAILED,
                    "error": str(exc),
                    "completed_at": failed_at,
                }
            )
            self._jobs[job_id] = failed

            await self._event_bus.publish(
                AnonymizationFailed(
                    job_id=failed.id,
                    job_name=failed.name,
                    error=str(exc),
                    records_processed=updated.records_processed,
                )
            )
            return failed

    async def get_job(self, job_id: str) -> AnonymizationJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise AnonymizationError(f"Job '{job_id}' not found")
        return job

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> tuple[AnonymizationJob, ...]:
        jobs = list(self._jobs.values())
        if status is not None:
            jobs = [j for j in jobs if j.status is status]
        return tuple(jobs[:limit])

    def _iter_source(self, source: str) -> list[dict[str, Any]]:
        return [{"source": source, "content": "sample"}]
