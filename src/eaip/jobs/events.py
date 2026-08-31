"""Job domain events — published via EventBus during job lifecycle."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class JobEvent(DomainEvent):
    """Base for job-related domain events."""


class JobScheduled(JobEvent):
    event_type: ClassVar[str] = "eaip.job.scheduled"
    job_id: str = ""
    job_name: str = ""
    schedule: str = ""
    priority: int = 0


class JobStarted(JobEvent):
    event_type: ClassVar[str] = "eaip.job.started"
    run_id: str = ""
    job_id: str = ""
    job_name: str = ""
    attempt: int = 0
    priority: int = 0


class JobProgress(JobEvent):
    event_type: ClassVar[str] = "eaip.job.progress"
    run_id: str = ""
    job_id: str = ""
    job_name: str = ""
    progress: float = 0.0
    message: str = ""


class JobCompleted(JobEvent):
    event_type: ClassVar[str] = "eaip.job.completed"
    run_id: str = ""
    job_id: str = ""
    job_name: str = ""
    attempt: int = 0
    duration_ms: float = 0.0
    result: str = ""


class JobFailed(JobEvent):
    event_type: ClassVar[str] = "eaip.job.failed"
    run_id: str = ""
    job_id: str = ""
    job_name: str = ""
    attempt: int = 0
    error: str = ""
    will_retry: bool = False


class JobStatusChanged(JobEvent):
    event_type: ClassVar[str] = "eaip.job.status_changed"
    run_id: str = ""
    job_id: str = ""
    job_name: str = ""
    status: str = ""


__all__ = [
    "JobCompleted",
    "JobEvent",
    "JobFailed",
    "JobProgress",
    "JobScheduled",
    "JobStarted",
    "JobStatusChanged",
]
