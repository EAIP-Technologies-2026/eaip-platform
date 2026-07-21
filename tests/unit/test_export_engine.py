"""Tests for the export engine."""

from __future__ import annotations

import pytest

from eaip.export.engine import ExportEngine
from eaip.export.exceptions import ReportNotFoundError
from eaip.export.models import ExportConfig, ReportDefinition


class TestRegisterReport:
    def test_register_new_report(self) -> None:
        engine = ExportEngine()
        r = ReportDefinition(id="r1", name="Report")
        result = engine.register_report(r)
        assert result.id == "r1"
        assert engine.get_report("r1").name == "Report"

    def test_register_overwrites_existing(self) -> None:
        engine = ExportEngine()
        r1 = ReportDefinition(id="r1", name="Original")
        r2 = ReportDefinition(id="r1", name="Updated")
        engine.register_report(r1)
        engine.register_report(r2)
        assert engine.get_report("r1").name == "Updated"

    def test_list_reports(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        engine.register_report(ReportDefinition(id="r2", name="R2"))
        reports = engine.list_reports()
        assert len(reports) == 2


class TestUnregisterReport:
    def test_unregister_existing(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        engine.unregister_report("r1")
        assert len(engine.list_reports()) == 0

    def test_unregister_missing_raises(self) -> None:
        engine = ExportEngine()
        with pytest.raises(ReportNotFoundError):
            engine.unregister_report("missing")


class TestGetReport:
    def test_get_existing(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        report = engine.get_report("r1")
        assert report.name == "R1"

    def test_get_missing_raises(self) -> None:
        engine = ExportEngine()
        with pytest.raises(ReportNotFoundError):
            engine.get_report("missing")


class TestCreateExportJob:
    def test_create_job(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        assert job.report_id == "r1"
        assert job.status == "pending"
        assert job.id is not None

    def test_create_job_with_custom_format(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1", format="xlsx")
        assert job.format == "xlsx"

    def test_create_job_for_missing_report_raises(self) -> None:
        engine = ExportEngine()
        with pytest.raises(ReportNotFoundError):
            engine.create_export_job("missing")


class TestGetJob:
    def test_get_existing_job(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        fetched = engine.get_job(job.id)
        assert fetched.id == job.id

    def test_get_missing_job_raises(self) -> None:
        engine = ExportEngine()
        with pytest.raises(ReportNotFoundError):
            engine.get_job("missing")


class TestCancelJob:
    def test_cancel_pending_job(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        cancelled = engine.cancel_job(job.id)
        assert cancelled.status == "failed"
        assert cancelled.error == "Cancelled by user"

    def test_cancel_completed_job_unchanged(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        completed = job.model_copy(update={"status": "completed"})
        engine._jobs[job.id] = completed
        result = engine.cancel_job(job.id)
        assert result.status == "completed"

    def test_cancel_missing_raises(self) -> None:
        engine = ExportEngine()
        with pytest.raises(ReportNotFoundError):
            engine.cancel_job("missing")


class TestListJobs:
    def test_list_all_jobs(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        engine.create_export_job("r1")
        engine.create_export_job("r1")
        assert len(engine.list_jobs()) == 2

    def test_list_jobs_filtered_by_report(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        engine.register_report(ReportDefinition(id="r2", name="R2"))
        engine.create_export_job("r1")
        engine.create_export_job("r2")
        engine.create_export_job("r2")
        jobs = engine.list_jobs(report_id="r2")
        assert len(jobs) == 2


class TestExecuteExport:
    def test_execute_export_success(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        result = engine.execute_export(job)
        assert result.status == "completed"
        assert result.record_count == 0
        assert result.duration_ms >= 0

    def test_execute_export_with_data(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        data = [{"col1": "val1", "col2": "val2"}, {"col1": "val3", "col2": "val4"}]
        result = engine.execute_export(job, data=data)
        assert result.status == "completed"
        assert result.record_count == 2
        assert result.file_size_bytes > 0

    def test_execute_export_job_updates_status(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        engine.execute_export(job)
        assert engine.get_job(job.id).status == "completed"

    def test_execute_report_convenience(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.execute_report("r1")
        assert job.status == "completed"

    def test_execute_report_with_format_override(self) -> None:
        engine = ExportEngine()
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.execute_report("r1", format="json")
        assert job.format == "json"
        assert job.status == "completed"

    def test_execute_report_missing_raises(self) -> None:
        engine = ExportEngine()
        with pytest.raises(ReportNotFoundError):
            engine.execute_report("missing")


class TestConfig:
    def test_default_config(self) -> None:
        engine = ExportEngine()
        assert engine.config.default_format == "csv"
        assert engine.config.max_concurrent_exports == 5

    def test_custom_config(self) -> None:
        config = ExportConfig(default_format="pdf", max_concurrent_exports=3)
        engine = ExportEngine(config=config)
        assert engine.config.default_format == "pdf"
        assert engine.config.max_concurrent_exports == 3


class TestEventHandlers:
    def test_event_handler_invoked_on_register(self) -> None:
        engine = ExportEngine()
        events: list[str] = []

        class Handler:
            def on_ReportRegistered(self, event: object) -> None:
                events.append("registered")

        engine.register_event_handler(Handler())
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        assert "registered" in events

    def test_event_handler_invoked_on_unregister(self) -> None:
        engine = ExportEngine()
        events: list[str] = []

        class Handler:
            def on_ReportUnregistered(self, event: object) -> None:
                events.append("unregistered")

        engine.register_event_handler(Handler())
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        engine.unregister_report("r1")
        assert "unregistered" in events

    def test_event_handler_on_export_completed(self) -> None:
        engine = ExportEngine()
        events: list[str] = []

        class Handler:
            def on_ExportCompleted(self, event: object) -> None:
                events.append("completed")

        engine.register_event_handler(Handler())
        engine.register_report(ReportDefinition(id="r1", name="R1"))
        job = engine.create_export_job("r1")
        engine.execute_export(job)
        assert "completed" in events
