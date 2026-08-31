"""Tests for batchjob domain events."""

from __future__ import annotations

from eaip.batchjob.events import BatchJobCompleted, BatchJobCreated, BatchJobFailed, BatchJobStarted
from eaip.events.event import DomainEvent


class TestBatchJobCreated:
    def test_event_type(self) -> None:
        event = BatchJobCreated(job_id="j1", name="Export", job_type="export", parameters={})
        assert event.event_type == "eaip.batchjob.created"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = BatchJobCreated(
            job_id="j1", name="Export", job_type="export", parameters={"format": "csv"}
        )
        assert event.job_id == "j1"
        assert event.name == "Export"
        assert event.job_type == "export"
        assert event.parameters == {"format": "csv"}


class TestBatchJobStarted:
    def test_event_type(self) -> None:
        event = BatchJobStarted(job_id="j1", execution_id="e1")
        assert event.event_type == "eaip.batchjob.started"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = BatchJobStarted(job_id="j1", execution_id="e1")
        assert event.job_id == "j1"
        assert event.execution_id == "e1"


class TestBatchJobCompleted:
    def test_event_type(self) -> None:
        event = BatchJobCompleted(job_id="j1", execution_id="e1", result={})
        assert event.event_type == "eaip.batchjob.completed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = BatchJobCompleted(job_id="j1", execution_id="e1", result={"rows": 100})
        assert event.job_id == "j1"
        assert event.result == {"rows": 100}


class TestBatchJobFailed:
    def test_event_type(self) -> None:
        event = BatchJobFailed(job_id="j1", execution_id="e1", error="Timeout", retry_count=2)
        assert event.event_type == "eaip.batchjob.failed"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = BatchJobFailed(job_id="j1", execution_id="e1", error="Timeout", retry_count=2)
        assert event.job_id == "j1"
        assert event.error == "Timeout"
        assert event.retry_count == 2


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(BatchJobCreated, DomainEvent)
        assert issubclass(BatchJobStarted, DomainEvent)
        assert issubclass(BatchJobCompleted, DomainEvent)
        assert issubclass(BatchJobFailed, DomainEvent)
