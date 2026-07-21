"""Tests for ReportScheduler."""

from __future__ import annotations

import pytest

from eaip.reportsched.exceptions import ReportGenerationError, ReportNotFoundError, SchedulerError
from eaip.reportsched.models import ReportDefinition, ReportFormat, SchedulerConfig
from eaip.reportsched.scheduler import ReportScheduler


class TestReportScheduler:
    @pytest.fixture
    def scheduler(self) -> ReportScheduler:
        return ReportScheduler()

    @pytest.fixture
    def sample_definition(self) -> ReportDefinition:
        return ReportDefinition(
            id="r1",
            name="Daily Report",
            report_type="summary",
            format=ReportFormat.PDF,
            schedule_cron="0 6 * * *",
            recipients=("admin@example.com",),
        )

    class TestCreateDefinition:
        async def test_creates_definition(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            result = await scheduler.create_definition(sample_definition)
            assert result.id == "r1"
            assert result.name == "Daily Report"

        async def test_stores_definition(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            stored = await scheduler.get_definition("r1")
            assert stored.id == "r1"

    class TestGetDefinition:
        async def test_returns_definition(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            result = await scheduler.get_definition("r1")
            assert result.report_type == "summary"

        async def test_raises_on_missing(self, scheduler: ReportScheduler) -> None:
            with pytest.raises(ReportNotFoundError):
                await scheduler.get_definition("nonexistent")

    class TestUpdateDefinition:
        async def test_updates_definition(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            updated = await scheduler.update_definition("r1", name="Updated Report")
            assert updated.name == "Updated Report"

        async def test_raises_on_missing(self, scheduler: ReportScheduler) -> None:
            with pytest.raises(ReportNotFoundError):
                await scheduler.update_definition("nonexistent", name="Test")

    class TestListDefinitions:
        async def test_empty_when_none(self, scheduler: ReportScheduler) -> None:
            assert await scheduler.list_definitions() == []

        async def test_returns_all(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            defs = await scheduler.list_definitions()
            assert len(defs) == 1

        async def test_filters_enabled(self, scheduler: ReportScheduler) -> None:
            d1 = ReportDefinition(id="d1", name="A", report_type="t", enabled=True)
            d2 = ReportDefinition(id="d2", name="B", report_type="t", enabled=False)
            await scheduler.create_definition(d1)
            await scheduler.create_definition(d2)
            result = await scheduler.list_definitions(enabled_only=True)
            assert len(result) == 1
            assert result[0].id == "d1"

    class TestGenerateReport:
        async def test_generates_report(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            execution = await scheduler.generate_report("r1")
            assert execution.status == "completed"
            assert execution.report_id == "r1"

        async def test_raises_on_missing_definition(self, scheduler: ReportScheduler) -> None:
            with pytest.raises(ReportNotFoundError):
                await scheduler.generate_report("nonexistent")

        async def test_raises_on_disabled(self, scheduler: ReportScheduler) -> None:
            d = ReportDefinition(id="d1", name="Disabled", report_type="t", enabled=False)
            await scheduler.create_definition(d)
            with pytest.raises(SchedulerError):
                await scheduler.generate_report("d1")

    class TestGetExecution:
        async def test_returns_execution(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            execution = await scheduler.generate_report("r1")
            result = await scheduler.get_execution(execution.id)
            assert result.id == execution.id

        async def test_raises_on_missing(self, scheduler: ReportScheduler) -> None:
            with pytest.raises(ReportNotFoundError):
                await scheduler.get_execution("nonexistent")

    class TestListExecutions:
        async def test_returns_executions(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            await scheduler.generate_report("r1")
            execs = await scheduler.list_executions()
            assert len(execs) == 1

        async def test_filters_by_status(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            await scheduler.generate_report("r1")
            result = await scheduler.list_executions(status="completed")
            assert len(result) == 1

    class TestGetStatistics:
        async def test_returns_stats(
            self, scheduler: ReportScheduler, sample_definition: ReportDefinition
        ) -> None:
            await scheduler.create_definition(sample_definition)
            stats = await scheduler.get_statistics()
            assert stats["total_definitions"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            s = ReportScheduler()
            assert s.config.max_concurrent_executions == 5

        def test_custom_config(self) -> None:
            cfg = SchedulerConfig(max_concurrent_executions=10)
            s = ReportScheduler(config=cfg)
            assert s.config.max_concurrent_executions == 10
