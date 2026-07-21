"""ImportExportService — import/export jobs, validation, format conversion, scheduling, reports."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from eaip.import_export.exceptions import (
    ExportError,
    ExportFormatError,
    ExportSchedulingError,
    ImportError,
    ImportMappingError,
    ImportValidationError,
)
from eaip.import_export.models import (
    ExportFormat,
    ExportJob,
    ExportJobStatus,
    ExportResult,
    FieldMapping,
    ImportExportAuditEntry,
    ImportExportConfig,
    ImportExportMapping,
    ImportExportMetrics,
    ImportExportReport,
    ImportExportSchedule,
    ImportExportValidation,
    ImportJob,
    ImportJobStatus,
    ImportRecord,
    ImportResult,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ImportExportService:
    """Central service managing import/export operations, validation, and scheduling."""

    def __init__(self, config: ImportExportConfig | None = None) -> None:
        self._config = config or ImportExportConfig()
        self._import_jobs: dict[str, ImportJob] = {}
        self._export_jobs: dict[str, ExportJob] = {}
        self._import_results: dict[str, ImportResult] = {}
        self._export_results: dict[str, ExportResult] = {}
        self._import_records: dict[str, ImportRecord] = {}
        self._mappings: dict[str, ImportExportMapping] = {}
        self._validations: dict[str, ImportExportValidation] = {}
        self._schedules: dict[str, ImportExportSchedule] = {}
        self._audit_entries: list[ImportExportAuditEntry] = []
        self._log = get_logger("eaip.import_export.service")

    @property
    def config(self) -> ImportExportConfig:
        return self._config

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    async def update_config(self, **changes: Any) -> ImportExportConfig:
        merged = {**self._config.model_dump(), **changes}
        self._config = ImportExportConfig(**merged)
        self._log.info("import_export.config.updated", changes=changes)
        return self._config

    # ------------------------------------------------------------------
    # Import Jobs
    # ------------------------------------------------------------------

    async def create_import_job(
        self,
        filename: str,
        source: str = "",
        format: str = "csv",
        mapping_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ImportJob:
        if not self._config.enable_validation and format not in self._config.allowed_formats:
            raise ImportError(f"format not allowed: {format!r}")

        job_id = f"import_{utc_now().timestamp():.0f}"
        job = ImportJob(
            id=job_id,
            filename=filename,
            source=source,
            format=format,
            mapping_id=mapping_id,
            metadata=metadata or {},
        )
        self._import_jobs[job_id] = job
        self._log.info("import_export.import_job.created", job_id=job_id, filename=filename)
        return job

    async def start_import_job(self, job_id: str) -> ImportJob:
        job = self._import_jobs.get(job_id)
        if job is None:
            raise ImportError(f"import job not found: {job_id!r}")
        updated = ImportJob(
            **{**job.model_dump(), "status": ImportJobStatus.RUNNING, "started_at": utc_now()}
        )
        self._import_jobs[job_id] = updated
        self._log.info("import_export.import_job.started", job_id=job_id)
        return updated

    async def complete_import_job(
        self,
        job_id: str,
        total_records: int = 0,
        imported_records: int = 0,
        failed_records: int = 0,
        errors: tuple[str, ...] = (),
    ) -> ImportJob:
        job = self._import_jobs.get(job_id)
        if job is None:
            raise ImportError(f"import job not found: {job_id!r}")
        now = utc_now()
        duration = int((now - (job.started_at or now)).total_seconds() * 1000)
        updated = ImportJob(
            **{
                **job.model_dump(),
                "status": ImportJobStatus.COMPLETED,
                "total_records": total_records,
                "processed_records": imported_records,
                "failed_records": failed_records,
                "completed_at": now,
                "duration_ms": duration,
            }
        )
        self._import_jobs[job_id] = updated
        result = ImportResult(
            job_id=job_id,
            success=not failed_records and not errors,
            total_records=total_records,
            imported_records=imported_records,
            failed_records=failed_records,
            errors=errors,
            duration_ms=duration,
        )
        self._import_results[job_id] = result
        self._log.info("import_export.import_job.completed", job_id=job_id)
        return updated

    async def fail_import_job(self, job_id: str, error: str) -> ImportJob:
        job = self._import_jobs.get(job_id)
        if job is None:
            raise ImportError(f"import job not found: {job_id!r}")
        now = utc_now()
        duration = int((now - (job.started_at or now)).total_seconds() * 1000)
        updated = ImportJob(
            **{
                **job.model_dump(),
                "status": ImportJobStatus.FAILED,
                "error": error,
                "completed_at": now,
                "duration_ms": duration,
            }
        )
        self._import_jobs[job_id] = updated
        result = ImportResult(
            job_id=job_id,
            success=False,
            total_records=job.total_records,
            errors=(error,),
            duration_ms=duration,
        )
        self._import_results[job_id] = result
        self._log.error("import_export.import_job.failed", job_id=job_id, error=error)
        return updated

    async def cancel_import_job(self, job_id: str) -> ImportJob:
        job = self._import_jobs.get(job_id)
        if job is None:
            raise ImportError(f"import job not found: {job_id!r}")
        now = utc_now()
        updated = ImportJob(
            **{
                **job.model_dump(),
                "status": ImportJobStatus.CANCELLED,
                "completed_at": now,
            }
        )
        self._import_jobs[job_id] = updated
        self._log.info("import_export.import_job.cancelled", job_id=job_id)
        return updated

    async def get_import_job(self, job_id: str) -> ImportJob:
        job = self._import_jobs.get(job_id)
        if job is None:
            raise ImportError(f"import job not found: {job_id!r}")
        return job

    async def list_import_jobs(self, status: ImportJobStatus | None = None) -> list[ImportJob]:
        results = list(self._import_jobs.values())
        if status:
            results = [j for j in results if j.status == status]
        return results

    async def get_import_result(self, job_id: str) -> ImportResult:
        result = self._import_results.get(job_id)
        if result is None:
            raise ImportError(f"import result not found: {job_id!r}")
        return result

    # ------------------------------------------------------------------
    # Import Records
    # ------------------------------------------------------------------

    async def process_import_record(
        self,
        job_id: str,
        record_id: str,
        row_number: int = 0,
        data: dict[str, Any] | None = None,
        valid: bool = True,
        errors: tuple[str, ...] = (),
    ) -> ImportRecord:
        record = ImportRecord(
            id=record_id,
            job_id=job_id,
            row_number=row_number,
            data=data or {},
            valid=valid,
            errors=errors,
            processed_at=utc_now(),
        )
        self._import_records[record_id] = record
        self._log.info(
            "import_export.import_record.processed",
            job_id=job_id,
            record_id=record_id,
            valid=valid,
        )
        return record

    async def list_import_records(
        self, job_id: str | None = None, valid: bool | None = None
    ) -> list[ImportRecord]:
        results = list(self._import_records.values())
        if job_id:
            results = [r for r in results if r.job_id == job_id]
        if valid is not None:
            results = [r for r in results if r.valid == valid]
        return results

    # ------------------------------------------------------------------
    # Export Jobs
    # ------------------------------------------------------------------

    async def create_export_job(
        self,
        query_id: str = "",
        format: ExportFormat = ExportFormat.CSV,
        filters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExportJob:
        job_id = f"export_{utc_now().timestamp():.0f}"
        job = ExportJob(
            id=job_id,
            query_id=query_id,
            format=format,
            filters=filters or {},
            metadata=metadata or {},
        )
        self._export_jobs[job_id] = job
        self._log.info("import_export.export_job.created", job_id=job_id)
        return job

    async def start_export_job(self, job_id: str) -> ExportJob:
        job = self._export_jobs.get(job_id)
        if job is None:
            raise ExportError(f"export job not found: {job_id!r}")
        updated = ExportJob(
            **{
                **job.model_dump(),
                "status": ExportJobStatus.RUNNING,
                "started_at": utc_now(),
            }
        )
        self._export_jobs[job_id] = updated
        self._log.info("import_export.export_job.started", job_id=job_id)
        return updated

    async def complete_export_job(
        self,
        job_id: str,
        record_count: int = 0,
        file_size_bytes: int = 0,
        output_path: str = "",
    ) -> ExportJob:
        job = self._export_jobs.get(job_id)
        if job is None:
            raise ExportError(f"export job not found: {job_id!r}")
        now = utc_now()
        duration = int((now - (job.started_at or now)).total_seconds() * 1000)
        updated = ExportJob(
            **{
                **job.model_dump(),
                "status": ExportJobStatus.COMPLETED,
                "completed_at": now,
                "duration_ms": duration,
                "record_count": record_count,
                "file_size_bytes": file_size_bytes,
                "output_path": output_path,
            }
        )
        self._export_jobs[job_id] = updated
        result = ExportResult(
            job_id=job_id,
            success=True,
            format=job.format,
            record_count=record_count,
            file_size_bytes=file_size_bytes,
            output_path=output_path,
            duration_ms=duration,
        )
        self._export_results[job_id] = result
        self._log.info("import_export.export_job.completed", job_id=job_id)
        return updated

    async def fail_export_job(self, job_id: str, error: str) -> ExportJob:
        job = self._export_jobs.get(job_id)
        if job is None:
            raise ExportError(f"export job not found: {job_id!r}")
        now = utc_now()
        duration = int((now - (job.started_at or now)).total_seconds() * 1000)
        updated = ExportJob(
            **{
                **job.model_dump(),
                "status": ExportJobStatus.FAILED,
                "error": error,
                "completed_at": now,
                "duration_ms": duration,
            }
        )
        self._export_jobs[job_id] = updated
        result = ExportResult(
            job_id=job_id,
            success=False,
            errors=(error,),
            duration_ms=duration,
        )
        self._export_results[job_id] = result
        self._log.error("import_export.export_job.failed", job_id=job_id, error=error)
        return updated

    async def cancel_export_job(self, job_id: str) -> ExportJob:
        job = self._export_jobs.get(job_id)
        if job is None:
            raise ExportError(f"export job not found: {job_id!r}")
        now = utc_now()
        updated = ExportJob(
            **{
                **job.model_dump(),
                "status": ExportJobStatus.CANCELLED,
                "completed_at": now,
            }
        )
        self._export_jobs[job_id] = updated
        self._log.info("import_export.export_job.cancelled", job_id=job_id)
        return updated

    async def get_export_job(self, job_id: str) -> ExportJob:
        job = self._export_jobs.get(job_id)
        if job is None:
            raise ExportError(f"export job not found: {job_id!r}")
        return job

    async def list_export_jobs(self, status: ExportJobStatus | None = None) -> list[ExportJob]:
        results = list(self._export_jobs.values())
        if status:
            results = [j for j in results if j.status == status]
        return results

    async def get_export_result(self, job_id: str) -> ExportResult:
        result = self._export_results.get(job_id)
        if result is None:
            raise ExportError(f"export result not found: {job_id!r}")
        return result

    # ------------------------------------------------------------------
    # Format Conversion
    # ------------------------------------------------------------------

    async def convert_format(self, job_id: str, source_format: str, target_format: str) -> bool:
        if target_format not in (f.value for f in ExportFormat):
            raise ExportFormatError(f"unsupported target format: {target_format!r}")
        if source_format not in (f.value for f in ExportFormat):
            raise ExportFormatError(f"unsupported source format: {source_format!r}")
        self._log.info(
            "import_export.export_format.converted",
            job_id=job_id,
            source=source_format,
            target=target_format,
        )
        return True

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    async def validate_import(
        self,
        job_id: str,
        records: list[dict[str, Any]],
        schema: dict[str, Any] | None = None,
    ) -> ImportExportValidation:
        validation_id = f"val_{utc_now().timestamp():.0f}"
        schema = schema or {}
        schema_errors: list[str] = []
        field_errors: list[str] = []
        warnings: list[str] = []

        for i, record in enumerate(records):
            for field, rules in schema.items():
                if rules.get("required", False) and field not in record:
                    field_errors.append(f"row {i}: missing required field {field!r}")
                if field in record:
                    val = record[field]
                    expected = rules.get("type", "string")
                    if expected == "number" and not isinstance(val, (int, float)):
                        tn = type(val).__name__
                        msg = f"row {i}: field {field!r} expected {expected}, got {tn}"
                        field_errors.append(msg)

        valid = not schema_errors and not field_errors
        validation = ImportExportValidation(
            id=validation_id,
            job_id=job_id,
            valid=valid,
            schema_errors=tuple(schema_errors),
            field_errors=tuple(field_errors),
            warnings=tuple(warnings),
            validated_records=len(records),
        )
        self._validations[validation_id] = validation
        self._log.info(
            "import_export.validation.completed",
            validation_id=validation_id,
            valid=valid,
        )
        return validation

    async def get_validation(self, validation_id: str) -> ImportExportValidation:
        validation = self._validations.get(validation_id)
        if validation is None:
            raise ImportValidationError(f"validation not found: {validation_id!r}")
        return validation

    # ------------------------------------------------------------------
    # Mappings
    # ------------------------------------------------------------------

    async def create_mapping(
        self,
        name: str,
        description: str = "",
        source_format: str = "",
        target_format: str = "",
        field_mappings: list[dict[str, Any]] | None = None,
        options: dict[str, Any] | None = None,
    ) -> ImportExportMapping:
        mapping_id = f"map_{utc_now().timestamp():.0f}"

        fields = tuple(FieldMapping(**fm) for fm in (field_mappings or []))
        mapping = ImportExportMapping(
            id=mapping_id,
            name=name,
            description=description,
            source_format=source_format,
            target_format=target_format,
            field_mappings=fields,
            options=options or {},
        )
        self._mappings[mapping_id] = mapping
        self._log.info("import_export.mapping.created", mapping_id=mapping_id)
        return mapping

    async def get_mapping(self, mapping_id: str) -> ImportExportMapping:
        mapping = self._mappings.get(mapping_id)
        if mapping is None:
            raise ImportMappingError(f"mapping not found: {mapping_id!r}")
        return mapping

    async def list_mappings(self) -> list[ImportExportMapping]:
        return list(self._mappings.values())

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    async def create_schedule(
        self,
        name: str,
        cron_expression: str,
        job_type: str = "import",
        description: str = "",
        mapping_id: str = "",
        config: dict[str, Any] | None = None,
    ) -> ImportExportSchedule:
        schedule_id = f"sched_{utc_now().timestamp():.0f}"
        schedule = ImportExportSchedule(
            id=schedule_id,
            name=name,
            description=description,
            job_type=job_type,
            cron_expression=cron_expression,
            mapping_id=mapping_id,
            config=config or {},
        )
        self._schedules[schedule_id] = schedule
        self._log.info("import_export.schedule.created", schedule_id=schedule_id)
        return schedule

    async def get_schedule(self, schedule_id: str) -> ImportExportSchedule:
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise ExportSchedulingError(f"schedule not found: {schedule_id!r}")
        return schedule

    async def list_schedules(self) -> list[ImportExportSchedule]:
        return list(self._schedules.values())

    async def trigger_schedule(self, schedule_id: str) -> bool:
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise ExportSchedulingError(f"schedule not found: {schedule_id!r}")
        self._log.info(
            "import_export.schedule.triggered",
            schedule_id=schedule_id,
            schedule_name=schedule.name,
        )
        return True

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    async def generate_report(self) -> ImportExportReport:
        report_id = f"report_{utc_now().timestamp():.0f}"
        imports = list(self._import_jobs.values())
        exports = list(self._export_jobs.values())

        total_imports = len(imports)
        successful_imports = len([j for j in imports if j.status == ImportJobStatus.COMPLETED])
        failed_imports = len([j for j in imports if j.status == ImportJobStatus.FAILED])
        total_exports = len(exports)
        successful_exports = len([j for j in exports if j.status == ExportJobStatus.COMPLETED])
        failed_exports = len([j for j in exports if j.status == ExportJobStatus.FAILED])
        total_records_imported = sum(j.processed_records for j in imports)
        total_records_exported = sum(j.record_count for j in exports)

        import_durations = [j.duration_ms for j in imports if j.duration_ms > 0]
        export_durations = [j.duration_ms for j in exports if j.duration_ms > 0]
        avg_import = sum(import_durations) / len(import_durations) if import_durations else 0.0
        avg_export = sum(export_durations) / len(export_durations) if export_durations else 0.0

        now = utc_now()
        metrics = ImportExportMetrics(
            total_imports=total_imports,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            total_exports=total_exports,
            successful_exports=successful_exports,
            failed_exports=failed_exports,
            total_records_imported=total_records_imported,
            total_records_exported=total_records_exported,
            avg_import_duration_ms=avg_import,
            avg_export_duration_ms=avg_export,
            period_start=now - timedelta(days=self._config.retention_days),
            period_end=now,
        )

        report = ImportExportReport(
            id=report_id,
            name=f"Import/Export Report {now.strftime('%Y-%m-%d')}",
            metrics=metrics,
            recent_jobs=tuple(
                {"id": j.id, "type": "import", "status": j.status.value}
                for j in sorted(imports, key=lambda x: x.created_at, reverse=True)[:10]
            )
            + tuple(
                {"id": j.id, "type": "export", "status": j.status.value}
                for j in sorted(exports, key=lambda x: x.created_at, reverse=True)[:10]
            ),
        )
        self._log.info("import_export.report.generated", report_id=report_id)
        return report

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    async def log_audit_entry(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user: str = "",
        details: dict[str, Any] | None = None,
    ) -> ImportExportAuditEntry:
        entry_id = f"audit_{utc_now().timestamp():.0f}"
        entry = ImportExportAuditEntry(
            id=entry_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            details=details or {},
        )
        self._audit_entries.append(entry)
        self._log.info(
            "import_export.audit.logged",
            entry_id=entry_id,
            action=action,
            entity_type=entity_type,
        )
        return entry

    async def list_audit_entries(
        self,
        entity_type: str | None = None,
        action: str | None = None,
    ) -> list[ImportExportAuditEntry]:
        results = list(self._audit_entries)
        if entity_type:
            results = [e for e in results if e.entity_type == entity_type]
        if action:
            results = [e for e in results if e.action == action]
        return results


__all__ = ["ImportExportService"]
