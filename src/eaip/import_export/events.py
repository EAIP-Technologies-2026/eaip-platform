"""Domain events for the import/export engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class ImportExportConfigUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.config.updated"


class ImportJobCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.import_job.created"
    job_id: str
    filename: str
    source: str = ""


class ImportJobStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.import_job.started"
    job_id: str
    filename: str


class ImportJobCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.import_job.completed"
    job_id: str
    filename: str
    total_records: int = 0
    imported_records: int = 0
    failed_records: int = 0
    duration_ms: int = 0


class ImportJobFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.import_job.failed"
    job_id: str
    filename: str
    error: str
    duration_ms: int = 0


class ImportJobCancelled(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.import_job.cancelled"
    job_id: str
    filename: str


class ImportRecordProcessed(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.import_record.processed"
    job_id: str
    record_id: str
    row_number: int = 0
    valid: bool = True
    errors: tuple[str, ...] = ()


class ExportJobCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.export_job.created"
    job_id: str
    query_id: str = ""


class ExportJobStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.export_job.started"
    job_id: str
    query_id: str = ""


class ExportJobCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.export_job.completed"
    job_id: str
    record_count: int = 0
    file_size_bytes: int = 0
    duration_ms: int = 0


class ExportJobFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.export_job.failed"
    job_id: str
    error: str
    duration_ms: int = 0


class ExportJobCancelled(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.export_job.cancelled"
    job_id: str


class ExportFormatConverted(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.export_format.converted"
    job_id: str
    source_format: str
    target_format: str


class ImportExportScheduleTriggered(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.schedule.triggered"
    schedule_id: str
    schedule_name: str
    job_type: str
    scheduled_time: datetime


class ImportExportValidationCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.validation.completed"
    validation_id: str
    job_id: str
    valid: bool = True
    errors: tuple[str, ...] = ()


class ImportExportValidationFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.validation.failed"
    validation_id: str
    job_id: str
    error: str


class ImportExportReportGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.report.generated"
    report_id: str
    report_name: str


class ImportExportAuditLogged(DomainEvent):
    event_type: ClassVar[str] = "eaip.import_export.audit.logged"
    entry_id: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any]


__all__ = [
    "ExportFormatConverted",
    "ExportJobCancelled",
    "ExportJobCompleted",
    "ExportJobCreated",
    "ExportJobFailed",
    "ExportJobStarted",
    "ImportExportAuditLogged",
    "ImportExportConfigUpdated",
    "ImportExportReportGenerated",
    "ImportExportScheduleTriggered",
    "ImportExportValidationCompleted",
    "ImportExportValidationFailed",
    "ImportJobCancelled",
    "ImportJobCompleted",
    "ImportJobCreated",
    "ImportJobFailed",
    "ImportJobStarted",
    "ImportRecordProcessed",
]
