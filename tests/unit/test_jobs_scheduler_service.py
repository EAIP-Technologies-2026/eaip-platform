from __future__ import annotations

import pytest

from eaip.jobs.scheduler_service import (
    CalendarDay,
    EnterpriseScheduler,
    ScheduledTask,
    TriggerType,
)


class TestEnterpriseScheduler:
    @pytest.fixture
    def scheduler(self) -> EnterpriseScheduler:
        return EnterpriseScheduler()

    def test_register_task(self, scheduler: EnterpriseScheduler) -> None:
        task = ScheduledTask(
            task_id="t1", name="test", trigger_type=TriggerType.INTERVAL, interval_seconds=3600
        )
        scheduler.register_task(task)
        assert scheduler.get_task("t1") is not None

    def test_unregister_task(self, scheduler: EnterpriseScheduler) -> None:
        task = ScheduledTask(task_id="t1", name="test", trigger_type=TriggerType.ONCE)
        scheduler.register_task(task)
        assert scheduler.unregister_task("t1") is True
        assert scheduler.get_task("t1") is None

    def test_unregister_nonexistent(self, scheduler: EnterpriseScheduler) -> None:
        assert scheduler.unregister_task("nonexistent") is False

    def test_list_tasks(self, scheduler: EnterpriseScheduler) -> None:
        scheduler.register_task(
            ScheduledTask(task_id="t1", name="a", trigger_type=TriggerType.ONCE)
        )
        scheduler.register_task(
            ScheduledTask(task_id="t2", name="b", trigger_type=TriggerType.ONCE)
        )
        assert len(scheduler.list_tasks()) == 2

    def test_get_due_tasks(self, scheduler: EnterpriseScheduler) -> None:
        scheduler.register_task(
            ScheduledTask(task_id="t1", name="test", trigger_type=TriggerType.ONCE)
        )
        due = scheduler.get_due_tasks()
        assert len(due) >= 1

    def test_mark_executed(self, scheduler: EnterpriseScheduler) -> None:
        task = ScheduledTask(
            task_id="t1", name="test", trigger_type=TriggerType.INTERVAL, interval_seconds=60
        )
        scheduler.register_task(task)
        scheduler.mark_executed("t1")
        assert task.run_count == 1
        assert task.last_run_at is not None

    def test_pause_resume(self, scheduler: EnterpriseScheduler) -> None:
        scheduler.register_task(
            ScheduledTask(task_id="t1", name="test", trigger_type=TriggerType.ONCE)
        )
        assert scheduler.pause_task("t1") is True
        assert scheduler.get_task("t1") is not None
        assert scheduler.get_task("t1").is_active is False
        assert scheduler.resume_task("t1") is True
        assert scheduler.get_task("t1").is_active is True

    def test_dependency_resolution(self, scheduler: EnterpriseScheduler) -> None:
        t1 = ScheduledTask(task_id="t1", name="setup", trigger_type=TriggerType.ONCE)
        t2 = ScheduledTask(
            task_id="t2", name="process", trigger_type=TriggerType.ONCE, dependencies=("t1",)
        )
        scheduler.register_task(t1)
        scheduler.register_task(t2)
        resolved = scheduler.resolve_dependencies("t2")
        assert "t1" in resolved
        assert "t2" in resolved

    def test_calendar_trigger(self, scheduler: EnterpriseScheduler) -> None:
        task = ScheduledTask(
            task_id="t1",
            name="weekly",
            trigger_type=TriggerType.CALENDAR,
            calendar_days=(CalendarDay.MONDAY,),
            calendar_time="09:00",
        )
        scheduler.register_task(task)
        scheduler.mark_executed("t1")
        assert task.next_run_at is not None
