"""Export engine — create/execute/manage export jobs, register/unregister reports."""

from __future__ import annotations

import time
import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from eaip.export.events import (
    ExportCompleted,
    ExportFailed,
    ExportStarted,
    ReportRegistered,
    ReportUnregistered,
)
from eaip.export.exceptions import ExportFailedError, ReportNotFoundError
from eaip.export.formats import FormatConverter
from eaip.export.models import ExportConfig, ExportJob, ReportDefinition


class ExportEngine:
    def __init__(self, config: ExportConfig | None = None) -> None:
        self._config = config or ExportConfig()
        self._reports: dict[str, ReportDefinition] = {}
        self._jobs: dict[str, ExportJob] = {}
        self._event_handlers: list[object] = []

    @property
    def config(self) -> ExportConfig:
        return self._config

    @property
    def reports(self) -> Mapping[str, ReportDefinition]:
        return dict(self._reports)

    @property
    def jobs(self) -> Mapping[str, ExportJob]:
        return dict(self._jobs)

    def register_event_handler(self, handler: object) -> None:
        self._event_handlers.append(handler)

    def _emit(self, event: object) -> None:
        for handler in self._event_handlers:
            method_name = type(event).__name__
            method = getattr(handler, f"on_{method_name}", None)
            if method:
                method(event)

    def register_report(self, report: ReportDefinition) -> ReportDefinition:
        self._reports[report.id] = report
        event = ReportRegistered(report=report)
        self._emit(event)
        return report

    def unregister_report(self, report_id: str) -> None:
        report = self._reports.pop(report_id, None)
        if report is None:
            raise ReportNotFoundError(f"Report not found: {report_id}")
        event = ReportUnregistered(report_id=report_id, report_name=report.name)
        self._emit(event)

    def list_reports(self) -> list[ReportDefinition]:
        return list(self._reports.values())

    def get_report(self, report_id: str) -> ReportDefinition:
        report = self._reports.get(report_id)
        if report is None:
            raise ReportNotFoundError(f"Report not found: {report_id}")
        return report

    def create_export_job(
        self,
        report_id: str,
        format: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> ExportJob:
        report = self.get_report(report_id)
        job = ExportJob(
            id=str(uuid.uuid4()),
            report_id=report_id,
            status="pending",
            format=format or report.format,
            filters=filters or {},
        )
        self._jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> ExportJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise ReportNotFoundError(f"Export job not found: {job_id}")
        return job

    def cancel_job(self, job_id: str) -> ExportJob:
        job = self.get_job(job_id)
        if job.status not in ("pending", "running"):
            return job
        updated = job.model_copy(update={"status": "failed", "error": "Cancelled by user"})
        self._jobs[job_id] = updated
        return updated

    def list_jobs(self, report_id: str | None = None) -> list[ExportJob]:
        if report_id:
            return [j for j in self._jobs.values() if j.report_id == report_id]
        return list(self._jobs.values())

    def execute_report(
        self, report_id: str, format: str | None = None, filters: dict[str, Any] | None = None
    ) -> ExportJob:
        self.get_report(report_id)
        job = self.create_export_job(report_id, format=format, filters=filters)
        return self.execute_export(job)

    def execute_export(self, job: ExportJob, data: list[dict[str, Any]] | None = None) -> ExportJob:
        started_at = datetime.now()
        start_epoch = time.time()

        event_start = ExportStarted(job_id=job.id, report_id=job.report_id, format=job.format)
        self._emit(event_start)

        running = job.model_copy(update={"status": "running", "started_at": started_at})
        self._jobs[job.id] = running

        try:
            result = FormatConverter.convert([], job.format)
            record_count = 0

            if data is not None:
                result = FormatConverter.convert(data, job.format)
                record_count = len(data)

            duration_ms = int((time.time() - start_epoch) * 1000)
            file_size = len(result) if isinstance(result, (str, bytes)) else 0
            output_path = f"{self._config.temp_directory}/{job.id}.{job.format}"

            completed = running.model_copy(
                update={
                    "status": "completed",
                    "completed_at": datetime.now(),
                    "duration_ms": duration_ms,
                    "file_size_bytes": file_size,
                    "record_count": record_count,
                    "output_path": output_path,
                }
            )
            self._jobs[job.id] = completed

            event_completed = ExportCompleted(
                job_id=job.id,
                report_id=job.report_id,
                format=job.format,
                record_count=record_count,
                file_size_bytes=file_size,
                duration_ms=duration_ms,
            )
            self._emit(event_completed)
            return completed

        except Exception as exc:
            duration_ms = int((time.time() - start_epoch) * 1000)
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "completed_at": datetime.now(),
                    "duration_ms": duration_ms,
                    "error": str(exc),
                }
            )
            self._jobs[job.id] = failed

            event_failed = ExportFailed(
                job_id=job.id,
                report_id=job.report_id,
                format=job.format,
                error=str(exc),
                duration_ms=duration_ms,
            )
            self._emit(event_failed)
            raise ExportFailedError(f"Export failed: {exc}") from exc


__all__ = ["ExportEngine"]
