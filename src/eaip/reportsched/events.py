"""Domain events for report scheduling."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.reportsched.models import ReportFormat


class ReportScheduled(DomainEvent):
    """Emitted when a report is scheduled for generation."""

    event_type: ClassVar[str] = "eaip.reportsched.report.scheduled"

    report_id: str
    name: str
    report_format: ReportFormat
    cron: str


class ReportGenerated(DomainEvent):
    """Emitted when a report has been successfully generated."""

    event_type: ClassVar[str] = "eaip.reportsched.report.generated"

    report_id: str
    execution_id: str
    output_path: str


class ReportFailed(DomainEvent):
    """Emitted when report generation fails."""

    event_type: ClassVar[str] = "eaip.reportsched.report.failed"

    report_id: str
    execution_id: str
    error: str


__all__ = [
    "ReportFailed",
    "ReportGenerated",
    "ReportScheduled",
]
