"""Tests for the Import/Export package."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.import_export.events import (
    ExportFormatConverted,
    ExportJobCancelled,
    ExportJobCompleted,
    ExportJobCreated,
    ExportJobFailed,
    ExportJobStarted,
    ImportExportAuditLogged,
    ImportExportConfigUpdated,
    ImportExportReportGenerated,
    ImportExportScheduleTriggered,
    ImportExportValidationCompleted,
    ImportExportValidationFailed,
    ImportJobCancelled,
    ImportJobCompleted,
    ImportJobCreated,
    ImportJobFailed,
    ImportJobStarted,
    ImportRecordProcessed,
)
from eaip.import_export.exceptions import (
    ExportError,
    ExportFormatError,
    ExportSchedulingError,
    ImportError,
    ImportExportConfigError,
    ImportExportError,
    ImportMappingError,
    ImportValidationError,
)
from eaip.import_export.models import (
    ExportFormat,
    ExportJob,
    ExportJobStatus,
    ExportResult,
    ImportExportConfig,
    ImportExportMapping,
    ImportJob,
    ImportJobStatus,
    ImportRecord,
    ImportResult,
)
from eaip.import_export.service import ImportExportService

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestImportExportConfig:
    def test_defaults(self) -> None:
        c = ImportExportConfig()
        assert c.max_file_size_bytes == 524_288_000
        assert c.retention_days == 90

    def test_frozen(self) -> None:
        c = ImportExportConfig()
        with pytest.raises(ValueError):
            c.max_file_size_bytes = 999


class TestImportJob:
    def test_defaults(self) -> None:
        j = ImportJob(id="j1", filename="test.csv")
        assert j.status == ImportJobStatus.PENDING
        assert j.processed_records == 0

    def test_frozen(self) -> None:
        j = ImportJob(id="j1", filename="test.csv")
        with pytest.raises(ValueError):
            j.status = ImportJobStatus.RUNNING


class TestImportResult:
    def test_defaults(self) -> None:
        r = ImportResult(job_id="j1")
        assert r.success is True
        assert r.imported_records == 0


class TestImportRecord:
    def test_create(self) -> None:
        r = ImportRecord(id="r1", job_id="j1", data={"name": "test"})
        assert r.row_number == 0
        assert r.valid is True


class TestExportJob:
    def test_defaults(self) -> None:
        j = ExportJob(id="e1")
        assert j.status == ExportJobStatus.PENDING
        assert j.format == ExportFormat.CSV

    def test_frozen(self) -> None:
        j = ExportJob(id="e1")
        with pytest.raises(ValueError):
            j.format = ExportFormat.JSON


class TestExportResult:
    def test_defaults(self) -> None:
        r = ExportResult(job_id="e1")
        assert r.success is True
        assert r.format == ExportFormat.CSV


class TestExportJobStatus:
    def test_values(self) -> None:
        assert ExportJobStatus.PENDING.value == "pending"
        assert ExportJobStatus.COMPLETED.value == "completed"
        assert ExportJobStatus.FAILED.value == "failed"


class TestImportJobStatus:
    def test_values(self) -> None:
        assert ImportJobStatus.PENDING.value == "pending"
        assert ImportJobStatus.VALIDATING.value == "validating"
        assert ImportJobStatus.CANCELLED.value == "cancelled"


class TestExportFormat:
    def test_values(self) -> None:
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.PARQUET.value == "parquet"


class TestImportExportMapping:
    def test_create(self) -> None:
        m = ImportExportMapping(id="m1", name="Test Mapping")
        assert m.field_mappings == ()


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestImportExportEvents:
    def test_config_updated(self) -> None:
        e = ImportExportConfigUpdated()
        assert e.event_type == "eaip.import_export.config.updated"

    def test_import_job_created(self) -> None:
        e = ImportJobCreated(job_id="j1", filename="test.csv")
        assert e.event_type == "eaip.import_export.import_job.created"

    def test_import_job_started(self) -> None:
        e = ImportJobStarted(job_id="j1", filename="test.csv")
        assert e.event_type == "eaip.import_export.import_job.started"

    def test_import_job_completed(self) -> None:
        e = ImportJobCompleted(job_id="j1", filename="test.csv")
        assert e.event_type == "eaip.import_export.import_job.completed"

    def test_import_job_failed(self) -> None:
        e = ImportJobFailed(job_id="j1", filename="test.csv", error="err")
        assert e.event_type == "eaip.import_export.import_job.failed"

    def test_import_job_cancelled(self) -> None:
        e = ImportJobCancelled(job_id="j1", filename="test.csv")
        assert e.event_type == "eaip.import_export.import_job.cancelled"

    def test_import_record_processed(self) -> None:
        e = ImportRecordProcessed(job_id="j1", record_id="r1")
        assert e.event_type == "eaip.import_export.import_record.processed"

    def test_export_job_created(self) -> None:
        e = ExportJobCreated(job_id="e1")
        assert e.event_type == "eaip.import_export.export_job.created"

    def test_export_job_started(self) -> None:
        e = ExportJobStarted(job_id="e1")
        assert e.event_type == "eaip.import_export.export_job.started"

    def test_export_job_completed(self) -> None:
        e = ExportJobCompleted(job_id="e1")
        assert e.event_type == "eaip.import_export.export_job.completed"

    def test_export_job_failed(self) -> None:
        e = ExportJobFailed(job_id="e1", error="err")
        assert e.event_type == "eaip.import_export.export_job.failed"

    def test_export_job_cancelled(self) -> None:
        e = ExportJobCancelled(job_id="e1")
        assert e.event_type == "eaip.import_export.export_job.cancelled"

    def test_export_format_converted(self) -> None:
        e = ExportFormatConverted(job_id="e1", source_format="csv", target_format="json")
        assert e.event_type == "eaip.import_export.export_format.converted"

    def test_schedule_triggered(self) -> None:
        e = ImportExportScheduleTriggered(
            schedule_id="s1",
            schedule_name="nightly",
            job_type="import",
            scheduled_time=datetime.now(),
        )
        assert e.event_type == "eaip.import_export.schedule.triggered"

    def test_validation_completed(self) -> None:
        e = ImportExportValidationCompleted(validation_id="v1", job_id="j1")
        assert e.event_type == "eaip.import_export.validation.completed"

    def test_validation_failed(self) -> None:
        e = ImportExportValidationFailed(validation_id="v1", job_id="j1", error="err")
        assert e.event_type == "eaip.import_export.validation.failed"

    def test_report_generated(self) -> None:
        e = ImportExportReportGenerated(report_id="r1", report_name="test")
        assert e.event_type == "eaip.import_export.report.generated"

    def test_audit_logged(self) -> None:
        e = ImportExportAuditLogged(
            entry_id="a1", action="create", entity_type="job", entity_id="j1", details={}
        )
        assert e.event_type == "eaip.import_export.audit.logged"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestImportExportExceptions:
    def test_base_error(self) -> None:
        e = ImportExportError("test")
        assert "test" in str(e)

    def test_import_error(self) -> None:
        e = ImportError("import error")
        assert isinstance(e, ImportExportError)

    def test_export_error(self) -> None:
        e = ExportError("export error")
        assert isinstance(e, ImportExportError)

    def test_import_validation_error(self) -> None:
        e = ImportValidationError("validation error")
        assert isinstance(e, ImportExportError)

    def test_export_format_error(self) -> None:
        e = ExportFormatError("format error")
        assert isinstance(e, ImportExportError)

    def test_import_mapping_error(self) -> None:
        e = ImportMappingError("mapping error")
        assert isinstance(e, ImportExportError)

    def test_export_scheduling_error(self) -> None:
        e = ExportSchedulingError("scheduling error")
        assert isinstance(e, ImportExportError)

    def test_config_error(self) -> None:
        e = ImportExportConfigError("config error")
        assert isinstance(e, ImportExportError)


# ---------------------------------------------------------------------------
# Service — Import Jobs
# ---------------------------------------------------------------------------


class TestImportExportServiceImports:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_create_import_job(self, service: ImportExportService) -> None:
        job = await service.create_import_job("data.csv", source="upload")
        assert job.filename == "data.csv"
        assert job.source == "upload"
        assert job.status == ImportJobStatus.PENDING

    async def test_get_import_job(self, service: ImportExportService) -> None:
        created = await service.create_import_job("data.csv")
        job = await service.get_import_job(created.id)
        assert job.id == created.id

    async def test_get_import_job_not_found(self, service: ImportExportService) -> None:
        with pytest.raises(ImportError):
            await service.get_import_job("nonexistent")

    async def test_start_import_job(self, service: ImportExportService) -> None:
        created = await service.create_import_job("data.csv")
        started = await service.start_import_job(created.id)
        assert started.status == ImportJobStatus.RUNNING
        assert started.started_at is not None

    async def test_complete_import_job(self, service: ImportExportService) -> None:
        created = await service.create_import_job("data.csv")
        await service.start_import_job(created.id)
        completed = await service.complete_import_job(
            created.id, total_records=100, imported_records=95
        )
        assert completed.status == ImportJobStatus.COMPLETED
        assert completed.processed_records == 95

    async def test_fail_import_job(self, service: ImportExportService) -> None:
        created = await service.create_import_job("data.csv")
        await service.start_import_job(created.id)
        failed = await service.fail_import_job(created.id, "parse error")
        assert failed.status == ImportJobStatus.FAILED
        assert failed.error == "parse error"

    async def test_cancel_import_job(self, service: ImportExportService) -> None:
        created = await service.create_import_job("data.csv")
        cancelled = await service.cancel_import_job(created.id)
        assert cancelled.status == ImportJobStatus.CANCELLED

    async def test_list_import_jobs(self, service: ImportExportService) -> None:
        await service.create_import_job("a.csv")
        await service.create_import_job("b.csv")
        jobs = await service.list_import_jobs()
        assert len(jobs) == 2

    async def test_list_import_jobs_filtered(self, service: ImportExportService) -> None:
        j1 = await service.create_import_job("a.csv")
        await service.cancel_import_job(j1.id)
        await service.create_import_job("b.csv")
        pending = await service.list_import_jobs(status=ImportJobStatus.PENDING)
        assert len(pending) == 1

    async def test_get_import_result(self, service: ImportExportService) -> None:
        created = await service.create_import_job("data.csv")
        await service.start_import_job(created.id)
        await service.complete_import_job(created.id, total_records=50, imported_records=50)
        result = await service.get_import_result(created.id)
        assert result.total_records == 50

    async def test_get_import_result_not_found(self, service: ImportExportService) -> None:
        with pytest.raises(ImportError):
            await service.get_import_result("nonexistent")


# ---------------------------------------------------------------------------
# Service — Import Records
# ---------------------------------------------------------------------------


class TestImportExportServiceRecords:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_process_import_record(self, service: ImportExportService) -> None:
        record = await service.process_import_record(
            "j1", "r1", row_number=1, data={"name": "test"}
        )
        assert record.valid is True
        assert record.data["name"] == "test"

    async def test_list_import_records(self, service: ImportExportService) -> None:
        await service.process_import_record("j1", "r1")
        await service.process_import_record("j1", "r2")
        records = await service.list_import_records(job_id="j1")
        assert len(records) == 2

    async def test_list_import_records_filtered(self, service: ImportExportService) -> None:
        await service.process_import_record("j1", "r1", valid=True)
        await service.process_import_record("j1", "r2", valid=False, errors=("bad",))
        valid = await service.list_import_records(valid=True)
        assert len(valid) == 1


# ---------------------------------------------------------------------------
# Service — Export Jobs
# ---------------------------------------------------------------------------


class TestImportExportServiceExports:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_create_export_job(self, service: ImportExportService) -> None:
        job = await service.create_export_job(query_id="q1", format=ExportFormat.JSON)
        assert job.query_id == "q1"
        assert job.format == ExportFormat.JSON
        assert job.status == ExportJobStatus.PENDING

    async def test_start_export_job(self, service: ImportExportService) -> None:
        created = await service.create_export_job()
        started = await service.start_export_job(created.id)
        assert started.status == ExportJobStatus.RUNNING

    async def test_complete_export_job(self, service: ImportExportService) -> None:
        created = await service.create_export_job()
        await service.start_export_job(created.id)
        completed = await service.complete_export_job(
            created.id, record_count=1000, file_size_bytes=5000
        )
        assert completed.status == ExportJobStatus.COMPLETED
        assert completed.record_count == 1000

    async def test_fail_export_job(self, service: ImportExportService) -> None:
        created = await service.create_export_job()
        await service.start_export_job(created.id)
        failed = await service.fail_export_job(created.id, "timeout")
        assert failed.status == ExportJobStatus.FAILED

    async def test_cancel_export_job(self, service: ImportExportService) -> None:
        created = await service.create_export_job()
        cancelled = await service.cancel_export_job(created.id)
        assert cancelled.status == ExportJobStatus.CANCELLED

    async def test_get_export_job(self, service: ImportExportService) -> None:
        created = await service.create_export_job()
        job = await service.get_export_job(created.id)
        assert job.id == created.id

    async def test_get_export_job_not_found(self, service: ImportExportService) -> None:
        with pytest.raises(ExportError):
            await service.get_export_job("nonexistent")

    async def test_list_export_jobs(self, service: ImportExportService) -> None:
        await service.create_export_job()
        await service.create_export_job()
        jobs = await service.list_export_jobs()
        assert len(jobs) == 2

    async def test_get_export_result(self, service: ImportExportService) -> None:
        created = await service.create_export_job()
        await service.start_export_job(created.id)
        await service.complete_export_job(created.id, record_count=500)
        result = await service.get_export_result(created.id)
        assert result.record_count == 500


# ---------------------------------------------------------------------------
# Service — Format Conversion
# ---------------------------------------------------------------------------


class TestImportExportServiceFormat:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_convert_format_valid(self, service: ImportExportService) -> None:
        result = await service.convert_format("e1", "csv", "json")
        assert result is True

    async def test_convert_format_invalid_target(self, service: ImportExportService) -> None:
        with pytest.raises(ExportFormatError):
            await service.convert_format("e1", "csv", "invalid")


# ---------------------------------------------------------------------------
# Service — Validation
# ---------------------------------------------------------------------------


class TestImportExportServiceValidation:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_validate_import_valid(self, service: ImportExportService) -> None:
        records = [{"name": "alice", "age": 30}, {"name": "bob", "age": 25}]
        schema = {"name": {"required": True, "type": "string"}, "age": {"type": "number"}}
        result = await service.validate_import("j1", records, schema)
        assert result.valid is True
        assert result.validated_records == 2

    async def test_validate_import_missing_field(self, service: ImportExportService) -> None:
        records = [{"name": "alice"}]
        schema = {
            "name": {"required": True, "type": "string"},
            "age": {"required": True, "type": "number"},
        }
        result = await service.validate_import("j1", records, schema)
        assert result.valid is False

    async def test_get_validation(self, service: ImportExportService) -> None:
        records = [{"name": "test"}]
        v = await service.validate_import("j1", records)
        result = await service.get_validation(v.id)
        assert result.id == v.id

    async def test_get_validation_not_found(self, service: ImportExportService) -> None:
        with pytest.raises(ImportValidationError):
            await service.get_validation("nonexistent")


# ---------------------------------------------------------------------------
# Service — Mappings
# ---------------------------------------------------------------------------


class TestImportExportServiceMappings:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_create_mapping(self, service: ImportExportService) -> None:
        fields = [{"source_field": "first_name", "target_field": "given_name"}]
        mapping = await service.create_mapping("Name Mapping", field_mappings=fields)
        assert mapping.name == "Name Mapping"
        assert len(mapping.field_mappings) == 1

    async def test_get_mapping(self, service: ImportExportService) -> None:
        created = await service.create_mapping("Test")
        mapping = await service.get_mapping(created.id)
        assert mapping.id == created.id

    async def test_get_mapping_not_found(self, service: ImportExportService) -> None:
        with pytest.raises(ImportMappingError):
            await service.get_mapping("nonexistent")

    async def test_list_mappings(self, service: ImportExportService) -> None:
        await service.create_mapping("M1")
        await service.create_mapping("M2")
        mappings = await service.list_mappings()
        assert len(mappings) == 2


# ---------------------------------------------------------------------------
# Service — Scheduling
# ---------------------------------------------------------------------------


class TestImportExportServiceSchedules:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_create_schedule(self, service: ImportExportService) -> None:
        sched = await service.create_schedule("Nightly", "0 0 * * *")
        assert sched.name == "Nightly"
        assert sched.cron_expression == "0 0 * * *"

    async def test_get_schedule(self, service: ImportExportService) -> None:
        created = await service.create_schedule("Daily", "0 6 * * *")
        sched = await service.get_schedule(created.id)
        assert sched.id == created.id

    async def test_get_schedule_not_found(self, service: ImportExportService) -> None:
        with pytest.raises(ExportSchedulingError):
            await service.get_schedule("nonexistent")

    async def test_list_schedules(self, service: ImportExportService) -> None:
        await service.create_schedule("S1", "0 0 * * *")
        await service.create_schedule("S2", "0 12 * * *")
        schedules = await service.list_schedules()
        assert len(schedules) == 2

    async def test_trigger_schedule(self, service: ImportExportService) -> None:
        created = await service.create_schedule("Test", "0 0 * * *")
        result = await service.trigger_schedule(created.id)
        assert result is True

    async def test_trigger_schedule_not_found(self, service: ImportExportService) -> None:
        with pytest.raises(ExportSchedulingError):
            await service.trigger_schedule("nonexistent")


# ---------------------------------------------------------------------------
# Service — Reports
# ---------------------------------------------------------------------------


class TestImportExportServiceReports:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_generate_report_empty(self, service: ImportExportService) -> None:
        report = await service.generate_report()
        assert report.metrics.total_imports == 0
        assert report.metrics.total_exports == 0

    async def test_generate_report_with_data(self, service: ImportExportService) -> None:
        job = await service.create_import_job("test.csv")
        await service.start_import_job(job.id)
        await service.complete_import_job(job.id, total_records=100, imported_records=100)
        report = await service.generate_report()
        assert report.metrics.total_imports == 1
        assert report.metrics.successful_imports == 1


# ---------------------------------------------------------------------------
# Service — Audit
# ---------------------------------------------------------------------------


class TestImportExportServiceAudit:
    @pytest.fixture
    def service(self) -> ImportExportService:
        return ImportExportService()

    async def test_log_audit_entry(self, service: ImportExportService) -> None:
        entry = await service.log_audit_entry("create", "job", "j1", user="admin")
        assert entry.action == "create"
        assert entry.user == "admin"

    async def test_list_audit_entries(self, service: ImportExportService) -> None:
        await service.log_audit_entry("create", "job", "j1")
        await service.log_audit_entry("delete", "mapping", "m1")
        entries = await service.list_audit_entries()
        assert len(entries) == 2

    async def test_list_audit_entries_filtered(self, service: ImportExportService) -> None:
        await service.log_audit_entry("create", "job", "j1")
        await service.log_audit_entry("delete", "mapping", "m1")
        jobs = await service.list_audit_entries(entity_type="job")
        assert len(jobs) == 1

    async def test_list_audit_entries_by_action(self, service: ImportExportService) -> None:
        await service.log_audit_entry("create", "job", "j1")
        await service.log_audit_entry("delete", "job", "j1")
        creates = await service.list_audit_entries(action="create")
        assert len(creates) == 1
