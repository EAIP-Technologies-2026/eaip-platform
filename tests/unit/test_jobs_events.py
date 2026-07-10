"""Tests for job domain events."""

from __future__ import annotations

from eaip.events.event import DomainEvent
from eaip.jobs.events import (
    JobCompleted,
    JobFailed,
    JobProgress,
    JobScheduled,
    JobStarted,
    JobStatusChanged,
)


class TestJobEvents:
    def test_job_scheduled(self) -> None:
        e = JobScheduled(job_id="j1", job_name="Test")
        assert e.event_type == "eaip.job.scheduled"
        assert isinstance(e, DomainEvent)

    def test_job_started(self) -> None:
        e = JobStarted(run_id="r1", job_id="j1", job_name="Test", attempt=1)
        assert e.event_type == "eaip.job.started"
        assert e.attempt == 1

    def test_job_progress(self) -> None:
        e = JobProgress(run_id="r1", job_id="j1", progress=0.5, message="half")
        assert e.event_type == "eaip.job.progress"
        assert e.progress == 0.5

    def test_job_completed(self) -> None:
        e = JobCompleted(run_id="r1", job_id="j1", duration_ms=100.0, result="ok")
        assert e.event_type == "eaip.job.completed"
        assert e.duration_ms == 100.0

    def test_job_failed(self) -> None:
        e = JobFailed(run_id="r1", job_id="j1", error="timeout", will_retry=True)
        assert e.event_type == "eaip.job.failed"
        assert e.will_retry is True

    def test_job_status_changed(self) -> None:
        e = JobStatusChanged(run_id="r1", job_id="j1", status="running")
        assert e.event_type == "eaip.job.status_changed"
        assert e.status == "running"
