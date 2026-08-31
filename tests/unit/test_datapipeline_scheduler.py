from __future__ import annotations

import pytest

from eaip.datapipeline.scheduler import PipelineScheduler


class TestPipelineScheduler:
    @pytest.fixture
    def scheduler(self) -> PipelineScheduler:
        return PipelineScheduler()

    @pytest.mark.asyncio
    async def test_schedule_pipeline(self, scheduler: PipelineScheduler) -> None:
        await scheduler.schedule_pipeline("p1", "0 * * * *")
        scheduled = await scheduler.get_scheduled("p1")
        assert scheduled is not None
        assert scheduled["cron_expression"] == "0 * * * *"
        assert scheduled["pipeline_id"] == "p1"

    @pytest.mark.asyncio
    async def test_schedule_invalid_cron(self, scheduler: PipelineScheduler) -> None:
        with pytest.raises(ValueError, match="Invalid cron"):
            await scheduler.schedule_pipeline("p1", "invalid cron")

    @pytest.mark.asyncio
    async def test_unschedule_pipeline(self, scheduler: PipelineScheduler) -> None:
        await scheduler.schedule_pipeline("p1", "0 * * * *")
        await scheduler.unschedule_pipeline("p1")
        result = await scheduler.get_scheduled("p1")
        assert result is None

    @pytest.mark.asyncio
    async def test_unschedule_nonexistent(self, scheduler: PipelineScheduler) -> None:
        await scheduler.unschedule_pipeline("nonexistent")

    @pytest.mark.asyncio
    async def test_check_due_pipelines(self, scheduler: PipelineScheduler) -> None:

        await scheduler.schedule_pipeline("p1", "* * * * *")
        scheduled = await scheduler.get_scheduled("p1")
        assert scheduled is not None
        assert scheduled["pipeline_id"] == "p1"

    @pytest.mark.asyncio
    async def test_check_due_no_schedules(self, scheduler: PipelineScheduler) -> None:
        due = await scheduler.check_due_pipelines()
        assert due == []

    @pytest.mark.asyncio
    async def test_get_scheduled_nonexistent(self, scheduler: PipelineScheduler) -> None:
        result = await scheduler.get_scheduled("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_scheduled_empty(self, scheduler: PipelineScheduler) -> None:
        assert await scheduler.list_scheduled() == []

    @pytest.mark.asyncio
    async def test_list_scheduled_multiple(self, scheduler: PipelineScheduler) -> None:
        await scheduler.schedule_pipeline("p1", "0 * * * *")
        await scheduler.schedule_pipeline("p2", "*/5 * * * *")
        schedules = await scheduler.list_scheduled()
        assert len(schedules) == 2

    @pytest.mark.asyncio
    async def test_schedule_updates_next_run(self, scheduler: PipelineScheduler) -> None:
        await scheduler.schedule_pipeline("p1", "0 0 * * *")
        scheduled = await scheduler.get_scheduled("p1")
        assert scheduled is not None
        assert "next_run" in scheduled
