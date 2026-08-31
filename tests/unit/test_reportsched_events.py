"""Tests for report scheduler domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.reportsched.events import ReportFailed, ReportGenerated, ReportScheduled
from eaip.reportsched.models import ReportFormat


class TestReportScheduled:
    def test_defaults(self) -> None:
        e = ReportScheduled(
            report_id="r1", name="Daily", report_format=ReportFormat.PDF, cron="0 6 * * *"
        )
        assert e.event_type == "eaip.reportsched.report.scheduled"
        assert isinstance(e, DomainEvent)

    def test_with_values(self) -> None:
        e = ReportScheduled(
            report_id="r1", name="Daily", report_format=ReportFormat.PDF, cron="0 6 * * *"
        )
        assert e.report_id == "r1"
        assert e.report_format == ReportFormat.PDF

    def test_frozen(self) -> None:
        e = ReportScheduled(
            report_id="r1", name="Daily", report_format=ReportFormat.PDF, cron="0 6 * * *"
        )
        with pytest.raises((ValueError, TypeError)):
            e.report_id = "r2"  # type: ignore[misc]


class TestReportGenerated:
    def test_defaults(self) -> None:
        e = ReportGenerated(report_id="r1", execution_id="e1", output_path="/tmp/r1.pdf")
        assert e.event_type == "eaip.reportsched.report.generated"
        assert e.output_path == "/tmp/r1.pdf"

    def test_with_values(self) -> None:
        e = ReportGenerated(report_id="r1", execution_id="e1", output_path="/tmp/r1.pdf")
        assert e.report_id == "r1"
        assert e.execution_id == "e1"


class TestReportFailed:
    def test_defaults(self) -> None:
        e = ReportFailed(report_id="r1", execution_id="e1", error="timeout")
        assert e.event_type == "eaip.reportsched.report.failed"
        assert e.error == "timeout"

    def test_with_values(self) -> None:
        e = ReportFailed(report_id="r1", execution_id="e1", error="timeout")
        assert e.report_id == "r1"
        assert e.error == "timeout"


class TestEventTypes:
    def test_all_have_unique_event_types(self) -> None:
        events = [ReportScheduled, ReportGenerated, ReportFailed]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))
