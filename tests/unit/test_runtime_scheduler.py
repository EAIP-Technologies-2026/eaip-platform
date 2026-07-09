from __future__ import annotations

import asyncio

import pytest

from eaip.runtime import Scheduler, TaskHandle


@pytest.fixture
def scheduler():
    return Scheduler()


class TestScheduler:
    async def test_schedule_once_executes(self, scheduler):
        events: list[str] = []

        async def task():
            events.append("ran")

        scheduler.once("test", delay_seconds=0.001, coro_fn=task)
        await scheduler.start()
        await asyncio.sleep(0.05)
        assert "ran" in events

    async def test_schedule_recurring_executes_multiple(self, scheduler):
        events: list[str] = []

        async def task():
            events.append("ran")

        scheduler.every("test", seconds=0.01, coro_fn=task)
        await scheduler.start()
        await asyncio.sleep(0.06)
        await scheduler.stop()
        assert len(events) >= 3

    async def test_cancel_prevents_execution(self, scheduler):
        events: list[str] = []

        async def task():
            events.append("ran")

        handle = scheduler.once("test", delay_seconds=0.1, coro_fn=task)
        await scheduler.start()
        scheduler.cancel(handle.id)
        await asyncio.sleep(0.2)
        assert "ran" not in events

    async def test_stop_clears_tasks(self, scheduler):
        async def task():
            pass

        scheduler.once("t1", delay_seconds=1, coro_fn=task)
        await scheduler.start()
        assert scheduler.task_count > 0
        await scheduler.stop()
        assert scheduler.task_count == 0

    async def test_task_failure_does_not_stop_scheduler(self, scheduler):
        events: list[str] = []

        async def failing():
            raise ValueError("boom")

        async def good():
            events.append("good")

        scheduler.every("fail", seconds=0.01, coro_fn=failing)
        scheduler.every("good", seconds=0.01, coro_fn=good)
        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()
        assert "good" in events

    async def test_task_handle_attributes(self):
        handle = TaskHandle(id="abc", name="test_task")
        assert handle.id == "abc"
        assert handle.name == "test_task"
        assert handle.cancelled is False
