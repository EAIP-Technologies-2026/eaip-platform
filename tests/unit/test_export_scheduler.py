"""Tests for the export scheduler."""

from __future__ import annotations

import pytest

from eaip.export.exceptions import ScheduleNotFoundError
from eaip.export.models import ReportDefinition
from eaip.export.scheduler import ExportScheduler


class TestScheduleReport:
    def test_schedule_report(self) -> None:
        scheduler = ExportScheduler()
        r = ReportDefinition(id="r1", name="R1", schedule_cron="0 0 * * *")
        scheduler.schedule_report(r)
        assert scheduler.scheduled_count == 1

    def test_schedule_overwrites_existing(self) -> None:
        scheduler = ExportScheduler()
        r1 = ReportDefinition(id="r1", name="Original", schedule_cron="0 0 * * *")
        r2 = ReportDefinition(id="r1", name="Updated", schedule_cron="0 0 * * *")
        scheduler.schedule_report(r1)
        scheduler.schedule_report(r2)
        assert scheduler.get_scheduled("r1").name == "Updated"
        assert scheduler.scheduled_count == 1


class TestUnscheduleReport:
    def test_unschedule_existing(self) -> None:
        scheduler = ExportScheduler()
        r = ReportDefinition(id="r1", name="R1", schedule_cron="0 0 * * *")
        scheduler.schedule_report(r)
        scheduler.unschedule_report("r1")
        assert scheduler.scheduled_count == 0

    def test_unschedule_missing_raises(self) -> None:
        scheduler = ExportScheduler()
        with pytest.raises(ScheduleNotFoundError):
            scheduler.unschedule_report("missing")


class TestListScheduled:
    def test_list_empty(self) -> None:
        scheduler = ExportScheduler()
        assert scheduler.list_scheduled() == []

    def test_list_scheduled_reports(self) -> None:
        scheduler = ExportScheduler()
        scheduler.schedule_report(ReportDefinition(id="r1", name="R1", schedule_cron="0 0 * * *"))
        scheduler.schedule_report(ReportDefinition(id="r2", name="R2", schedule_cron="0 0 * * *"))
        assert len(scheduler.list_scheduled()) == 2


class TestGetScheduled:
    def test_get_existing(self) -> None:
        scheduler = ExportScheduler()
        r = ReportDefinition(id="r1", name="R1", schedule_cron="0 0 * * *")
        scheduler.schedule_report(r)
        fetched = scheduler.get_scheduled("r1")
        assert fetched.name == "R1"

    def test_get_missing_raises(self) -> None:
        scheduler = ExportScheduler()
        with pytest.raises(ScheduleNotFoundError):
            scheduler.get_scheduled("missing")


class TestCheckDueExports:
    def test_due_exports_returns_enabled_with_cron(self) -> None:
        scheduler = ExportScheduler()
        scheduler.schedule_report(
            ReportDefinition(id="r1", name="R1", schedule_cron="0 0 * * *", enabled=True)
        )
        scheduler.schedule_report(
            ReportDefinition(id="r2", name="R2", schedule_cron="", enabled=True)
        )
        scheduler.schedule_report(
            ReportDefinition(id="r3", name="R3", schedule_cron="0 0 * * *", enabled=False)
        )
        due = scheduler.check_due_exports()
        assert len(due) == 1
        assert due[0].id == "r1"

    def test_no_due_when_no_cron(self) -> None:
        scheduler = ExportScheduler()
        scheduler.schedule_report(ReportDefinition(id="r1", name="R1"))
        due = scheduler.check_due_exports()
        assert due == []


class TestJobCount:
    def test_increment_count(self) -> None:
        scheduler = ExportScheduler()
        scheduler.schedule_report(ReportDefinition(id="r1", name="R1"))
        assert scheduler.increment_job_count("r1") == 1
        assert scheduler.increment_job_count("r1") == 2

    def test_get_count_default(self) -> None:
        scheduler = ExportScheduler()
        scheduler.schedule_report(ReportDefinition(id="r1", name="R1"))
        assert scheduler.get_job_count("r1") == 0

    def test_count_after_unschedule(self) -> None:
        scheduler = ExportScheduler()
        scheduler.schedule_report(ReportDefinition(id="r1", name="R1"))
        scheduler.increment_job_count("r1")
        scheduler.unschedule_report("r1")
        assert scheduler.scheduled_count == 0
