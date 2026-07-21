"""Enterprise scheduler — distributed scheduling, calendar-based, dependency resolution."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from eaip.jobs.events import JobScheduled
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class TriggerType(StrEnum):
    CRON = "cron"
    INTERVAL = "interval"
    CALENDAR = "calendar"
    ONCE = "once"


class CalendarDay(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ScheduledTask:
    def __init__(
        self,
        task_id: str,
        name: str,
        trigger_type: TriggerType,
        cron_expr: str = "",
        interval_seconds: int = 0,
        calendar_days: tuple[CalendarDay, ...] = (),
        calendar_time: str = "09:00",
        timezone: str = "UTC",
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self.task_id = task_id
        self.name = name
        self.trigger_type = trigger_type
        self.cron_expr = cron_expr
        self.interval_seconds = interval_seconds
        self.calendar_days = calendar_days
        self.calendar_time = calendar_time
        self.timezone = timezone
        self.dependencies = dependencies
        self.last_run_at: datetime | None = None
        self.next_run_at: datetime | None = None
        self.is_active: bool = True
        self.run_count: int = 0
        self.metadata: dict[str, Any] = {}


class EnterpriseScheduler:
    def __init__(self, event_bus: Any = None) -> None:
        self._tasks: dict[str, ScheduledTask] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.jobs.scheduler_service")

    def register_task(self, task: ScheduledTask) -> ScheduledTask:
        self._tasks[task.task_id] = task
        self._publish_event(JobScheduled(job_id=task.task_id, schedule=task.trigger_type.value))
        self._log.info("task.registered", task_id=task.task_id, trigger=task.trigger_type.value)
        return task

    def unregister_task(self, task_id: str) -> bool:
        task = self._tasks.pop(task_id, None)
        if task is not None:
            self._log.info("task.unregistered", task_id=task_id)
            return True
        return False

    def get_task(self, task_id: str) -> ScheduledTask | None:
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[ScheduledTask]:
        return list(self._tasks.values())

    def get_due_tasks(self, reference_time: datetime | None = None) -> list[ScheduledTask]:
        now = reference_time or utc_now()
        due: list[ScheduledTask] = []
        for task in self._tasks.values():
            if not task.is_active:
                continue
            if not self._dependencies_satisfied(task):
                continue
            if task.next_run_at is None or now >= task.next_run_at:
                due.append(task)
        return due

    def mark_executed(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return
        task.last_run_at = utc_now()
        task.run_count += 1
        task.next_run_at = self._compute_next_run(task)

    def pause_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.is_active = False
        return True

    def resume_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.is_active = True
        return True

    def resolve_dependencies(self, task_id: str) -> list[str]:
        resolved: list[str] = []
        visited: set[str] = set()

        def _resolve(tid: str) -> None:
            if tid in visited:
                return
            visited.add(tid)
            task = self._tasks.get(tid)
            if task is not None:
                for dep in task.dependencies:
                    _resolve(dep)
                resolved.append(tid)

        _resolve(task_id)
        return resolved

    def _dependencies_satisfied(self, task: ScheduledTask) -> bool:
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if dep is None:
                return False
            if dep.last_run_at is None or (
                task.last_run_at is not None and dep.last_run_at < task.last_run_at
            ):
                return False
        return True

    def _compute_next_run(self, task: ScheduledTask) -> datetime:
        now = utc_now()
        if task.trigger_type == TriggerType.INTERVAL and task.interval_seconds > 0:
            return now + timedelta(seconds=task.interval_seconds)
        if task.trigger_type == TriggerType.ONCE:
            return now + timedelta(days=365 * 100)
        if task.trigger_type == TriggerType.CALENDAR and task.calendar_days:
            day_map = {
                CalendarDay.MONDAY: 0,
                CalendarDay.TUESDAY: 1,
                CalendarDay.WEDNESDAY: 2,
                CalendarDay.THURSDAY: 3,
                CalendarDay.FRIDAY: 4,
                CalendarDay.SATURDAY: 5,
                CalendarDay.SUNDAY: 6,
            }
            target_days = {day_map.get(d, 0) for d in task.calendar_days}
            for i in range(1, 8):
                candidate = now + timedelta(days=i)
                if candidate.weekday() in target_days:
                    hour, minute = (task.calendar_time.split(":") + ["00", "00"])[:2]
                    return candidate.replace(
                        hour=int(hour), minute=int(minute), second=0, microsecond=0
                    )
        return now + timedelta(hours=1)

    def _publish_event(self, event: Any) -> None:
        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(self._event_bus.publish(event))
            except Exception:
                pass


__all__ = [
    "CalendarDay",
    "EnterpriseScheduler",
    "ScheduledTask",
    "TriggerType",
]
