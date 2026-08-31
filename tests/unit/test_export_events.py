"""Tests for export domain events."""

from __future__ import annotations

from datetime import UTC, datetime

from eaip.events.event import DomainEvent
from eaip.export.events import (
    ExportCompleted,
    ExportDelivered,
    ExportDeliveryFailed,
    ExportFailed,
    ExportScheduled,
    ExportStarted,
    ReportRegistered,
    ReportUnregistered,
)
from eaip.export.models import ReportDefinition


class TestReportRegistered:
    def test_event_type(self) -> None:
        r = ReportDefinition(id="r1", name="Report")
        event = ReportRegistered(report=r)
        assert event.event_type == "export.report.registered"
        assert isinstance(event, DomainEvent)

    def test_report_content(self) -> None:
        r = ReportDefinition(id="r1", name="Test Report")
        event = ReportRegistered(report=r)
        assert event.report.id == "r1"
        assert event.report.name == "Test Report"


class TestReportUnregistered:
    def test_event_type(self) -> None:
        event = ReportUnregistered(report_id="r1", report_name="Report")
        assert event.event_type == "export.report.unregistered"

    def test_fields(self) -> None:
        event = ReportUnregistered(report_id="r1", report_name="Monthly Report")
        assert event.report_id == "r1"
        assert event.report_name == "Monthly Report"


class TestExportStarted:
    def test_event_type(self) -> None:
        event = ExportStarted(job_id="j1", report_id="r1", format="csv")
        assert event.event_type == "export.job.started"

    def test_fields(self) -> None:
        event = ExportStarted(job_id="j1", report_id="r1", format="xlsx")
        assert event.job_id == "j1"
        assert event.format == "xlsx"


class TestExportCompleted:
    def test_event_type(self) -> None:
        event = ExportCompleted(
            job_id="j1",
            report_id="r1",
            format="csv",
            record_count=100,
            file_size_bytes=5000,
            duration_ms=150,
        )
        assert event.event_type == "export.job.completed"

    def test_fields(self) -> None:
        event = ExportCompleted(
            job_id="j1",
            report_id="r1",
            format="csv",
            record_count=50,
            file_size_bytes=2000,
            duration_ms=120,
        )
        assert event.record_count == 50
        assert event.duration_ms == 120


class TestExportFailed:
    def test_event_type(self) -> None:
        event = ExportFailed(
            job_id="j1", report_id="r1", format="csv", error="timeout", duration_ms=5000
        )
        assert event.event_type == "export.job.failed"

    def test_fields(self) -> None:
        event = ExportFailed(
            job_id="j1", report_id="r1", format="csv", error="Connection refused", duration_ms=3000
        )
        assert event.error == "Connection refused"
        assert event.duration_ms == 3000


class TestExportDelivered:
    def test_event_type(self) -> None:
        event = ExportDelivered(
            job_id="j1", channel="email", recipient="a@b.com", status="delivered"
        )
        assert event.event_type == "export.delivery.completed"

    def test_fields(self) -> None:
        event = ExportDelivered(
            job_id="j1", channel="webhook", recipient="https://hook.ex", status="sent"
        )
        assert event.channel == "webhook"
        assert event.status == "sent"


class TestExportDeliveryFailed:
    def test_event_type(self) -> None:
        event = ExportDeliveryFailed(
            job_id="j1", channel="email", recipient="a@b.com", error="SMTP error"
        )
        assert event.event_type == "export.delivery.failed"

    def test_fields(self) -> None:
        event = ExportDeliveryFailed(
            job_id="j1", channel="webhook", recipient="https://hook.ex", error="HTTP 500"
        )
        assert event.error == "HTTP 500"


class TestExportScheduled:
    def test_event_type(self) -> None:
        now = datetime.now(UTC)
        event = ExportScheduled(
            report_id="r1", report_name="Report", cron_expression="0 0 * * *", next_run=now
        )
        assert event.event_type == "export.report.scheduled"

    def test_fields(self) -> None:
        now = datetime.now(UTC)
        event = ExportScheduled(
            report_id="r1", report_name="Monthly", cron_expression="0 0 1 * *", next_run=now
        )
        assert event.cron_expression == "0 0 1 * *"
        assert event.report_name == "Monthly"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(ReportRegistered, DomainEvent)
        assert issubclass(ReportUnregistered, DomainEvent)
        assert issubclass(ExportStarted, DomainEvent)
        assert issubclass(ExportCompleted, DomainEvent)
        assert issubclass(ExportFailed, DomainEvent)
        assert issubclass(ExportDelivered, DomainEvent)
        assert issubclass(ExportDeliveryFailed, DomainEvent)
        assert issubclass(ExportScheduled, DomainEvent)
