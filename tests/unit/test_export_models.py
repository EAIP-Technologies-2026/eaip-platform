"""Tests for export domain models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.export.models import (
    DeliveryConfig,
    ExportConfig,
    ExportJob,
    FormatConfig,
    ReportDefinition,
    ScheduleConfig,
)


class TestReportDefinition:
    def test_minimal_creation(self) -> None:
        r = ReportDefinition(id="r1", name="Cost Report")
        assert r.id == "r1"
        assert r.name == "Cost Report"
        assert r.source_type == "custom"
        assert r.format == "csv"
        assert r.enabled is True

    def test_full_creation(self) -> None:
        r = ReportDefinition(
            id="r2",
            name="Monthly Analytics",
            description="Monthly analytics export",
            source_type="analytics",
            query_config={"metric": "users", "period": "monthly"},
            format="xlsx",
            schedule_cron="0 0 1 * *",
            recipients=("admin@eaip.dev",),
            tags=("analytics", "monthly"),
            metadata={"department": "engineering"},
        )
        assert r.source_type == "analytics"
        assert r.query_config["metric"] == "users"
        assert r.format == "xlsx"
        assert r.schedule_cron == "0 0 1 * *"
        assert r.recipients == ("admin@eaip.dev",)

    def test_frozen(self) -> None:
        r = ReportDefinition(id="r1", name="Report")
        with pytest.raises(ValidationError):
            r.name = "Changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ReportDefinition(id="r1", name="R1", invalid_field="x")  # type: ignore[call-arg]

    def test_default_timestamps(self) -> None:
        r = ReportDefinition(id="r1", name="Report")
        assert isinstance(r.created_at, datetime)
        assert isinstance(r.updated_at, datetime)

    def test_enabled_default_true(self) -> None:
        r = ReportDefinition(id="r1", name="Report")
        assert r.enabled is True

    def test_schedule_cron_default_empty(self) -> None:
        r = ReportDefinition(id="r1", name="Report")
        assert r.schedule_cron == ""

    def test_tags_empty_tuple(self) -> None:
        r = ReportDefinition(id="r1", name="Report")
        assert r.tags == ()


class TestExportJob:
    def test_minimal_creation(self) -> None:
        j = ExportJob(id="j1", report_id="r1")
        assert j.id == "j1"
        assert j.report_id == "r1"
        assert j.status == "pending"
        assert j.format == "csv"

    def test_full_creation(self) -> None:
        now = datetime.now(UTC)
        j = ExportJob(
            id="j1",
            report_id="r1",
            status="running",
            format="xlsx",
            filters={"date_from": "2025-01-01"},
            started_at=now,
            record_count=100,
            file_size_bytes=5000,
            output_path="/tmp/exports/j1.xlsx",
        )
        assert j.status == "running"
        assert j.record_count == 100
        assert j.file_size_bytes == 5000

    def test_frozen(self) -> None:
        j = ExportJob(id="j1", report_id="r1")
        with pytest.raises(ValidationError):
            j.status = "completed"

    def test_delivery_status_default(self) -> None:
        j = ExportJob(id="j1", report_id="r1")
        assert j.delivery_status == {}

    def test_error_default(self) -> None:
        j = ExportJob(id="j1", report_id="r1")
        assert j.error == ""


class TestFormatConfig:
    def test_default_csv(self) -> None:
        fc = FormatConfig()
        assert fc.csv["delimiter"] == ","
        assert fc.csv["include_headers"] is True
        assert fc.csv["encoding"] == "utf-8"

    def test_default_json(self) -> None:
        fc = FormatConfig()
        assert fc.json_format["indent"] == 2
        assert fc.json_format["include_schema"] is False

    def test_default_xlsx(self) -> None:
        fc = FormatConfig()
        assert fc.xlsx["sheet_name"] == "Export"
        assert fc.xlsx["freeze_panes"] is True

    def test_default_pdf(self) -> None:
        fc = FormatConfig()
        assert fc.pdf["orientation"] == "landscape"
        assert fc.pdf["page_size"] == "A4"

    def test_frozen(self) -> None:
        fc = FormatConfig()
        with pytest.raises(ValidationError):
            fc.csv = {"delimiter": "|"}


class TestScheduleConfig:
    def test_minimal_creation(self) -> None:
        sc = ScheduleConfig(cron_expression="0 0 * * *")
        assert sc.cron_expression == "0 0 * * *"
        assert sc.timezone == "UTC"
        assert sc.max_runs == 0

    def test_frozen(self) -> None:
        sc = ScheduleConfig(cron_expression="0 0 * * *")
        with pytest.raises(ValidationError):
            sc.timezone = "US/Eastern"


class TestDeliveryConfig:
    def test_minimal_creation(self) -> None:
        dc = DeliveryConfig()
        assert dc.channels == ("storage",)
        assert dc.retention_days == 30
        assert dc.compress is False

    def test_with_email(self) -> None:
        dc = DeliveryConfig(
            channels=("email", "storage"),
            email_recipients=("user@eaip.dev",),
            storage_path="/exports/",
        )
        assert "email" in dc.channels
        assert dc.email_recipients == ("user@eaip.dev",)

    def test_frozen(self) -> None:
        dc = DeliveryConfig()
        with pytest.raises(ValidationError):
            dc.retention_days = 60


class TestExportConfig:
    def test_minimal_creation(self) -> None:
        ec = ExportConfig()
        assert ec.max_file_size_bytes == 104_857_600
        assert ec.default_format == "csv"
        assert ec.max_concurrent_exports == 5
        assert ec.retention_days == 90

    def test_custom_values(self) -> None:
        ec = ExportConfig(
            max_file_size_bytes=50_000_000,
            default_format="xlsx",
            max_concurrent_exports=10,
        )
        assert ec.max_file_size_bytes == 50_000_000
        assert ec.default_format == "xlsx"
        assert ec.max_concurrent_exports == 10

    def test_frozen(self) -> None:
        ec = ExportConfig()
        with pytest.raises(ValidationError):
            ec.default_format = "pdf"
