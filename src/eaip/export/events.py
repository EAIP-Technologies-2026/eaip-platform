"""Domain events for the export & reporting engine."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from eaip.events.event import DomainEvent
from eaip.export.models import ReportDefinition


class ReportRegistered(DomainEvent):
    event_type: ClassVar[str] = "export.report.registered"
    report: ReportDefinition


class ReportUnregistered(DomainEvent):
    event_type: ClassVar[str] = "export.report.unregistered"
    report_id: str
    report_name: str


class ExportStarted(DomainEvent):
    event_type: ClassVar[str] = "export.job.started"
    job_id: str
    report_id: str
    format: str


class ExportCompleted(DomainEvent):
    event_type: ClassVar[str] = "export.job.completed"
    job_id: str
    report_id: str
    format: str
    record_count: int
    file_size_bytes: int
    duration_ms: int


class ExportFailed(DomainEvent):
    event_type: ClassVar[str] = "export.job.failed"
    job_id: str
    report_id: str
    format: str
    error: str
    duration_ms: int


class ExportDelivered(DomainEvent):
    event_type: ClassVar[str] = "export.delivery.completed"
    job_id: str
    channel: str
    recipient: str
    status: str


class ExportDeliveryFailed(DomainEvent):
    event_type: ClassVar[str] = "export.delivery.failed"
    job_id: str
    channel: str
    recipient: str
    error: str


class ExportScheduled(DomainEvent):
    event_type: ClassVar[str] = "export.report.scheduled"
    report_id: str
    report_name: str
    cron_expression: str
    next_run: datetime


__all__ = [
    "ExportCompleted",
    "ExportDelivered",
    "ExportDeliveryFailed",
    "ExportFailed",
    "ExportScheduled",
    "ExportStarted",
    "ReportRegistered",
    "ReportUnregistered",
]
