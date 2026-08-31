"""Enterprise task queue — priority queues, task scheduling, SLA tracking, worker pools."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Task:
    def __init__(
        self,
        task_id: str,
        name: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        sla_seconds: int = 0,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.task_id = task_id
        self.name = name
        self.priority = priority
        self.sla_seconds = sla_seconds
        self.payload = payload or {}
        self.status = TaskStatus.PENDING
        self.created_at = utc_now()
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.worker_id: str = ""
        self.error: str = ""
        self.retry_count: int = 0
        self.max_retries: int = 3


class EnterpriseTaskQueue:
    def __init__(self, event_bus: Any = None) -> None:
        self._tasks: dict[str, Task] = {}
        self._queue: list[Task] = []
        self._workers: set[str] = set()
        self._event_bus = event_bus
        self._log = get_logger("eaip.queue.task_queue")
        self._sla_violations: list[Task] = []

    def enqueue(self, task: Task) -> Task:
        self._tasks[task.task_id] = task
        self._queue.append(task)
        self._queue.sort(key=lambda t: _priority_value(t.priority), reverse=True)
        return task

    def enqueue_batch(self, tasks: list[Task]) -> list[Task]:
        for t in tasks:
            self.enqueue(t)
        return tasks

    def dequeue(self, worker_id: str) -> Task | None:
        if not self._queue:
            return None
        self._workers.add(worker_id)
        task = self._queue.pop(0)
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        task.worker_id = worker_id
        return task

    def complete(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.status = TaskStatus.COMPLETED
        task.completed_at = utc_now()
        self._check_sla(task)
        return True

    def fail(self, task_id: str, error: str = "") -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            self._queue.append(task)
            self._queue.sort(key=lambda t: _priority_value(t.priority), reverse=True)
        else:
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = utc_now()
        return True

    def peek(self, limit: int = 10) -> list[Task]:
        return self._queue[:limit]

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        if status:
            return [t for t in self._tasks.values() if t.status == status]
        return list(self._tasks.values())

    def get_queue_depth(self) -> int:
        return len(self._queue)

    def get_worker_count(self) -> int:
        return len(self._workers)

    def _check_sla(self, task: Task) -> None:
        if task.sla_seconds > 0 and task.started_at is not None:
            elapsed = (task.completed_at or utc_now()) - task.started_at
            if elapsed > timedelta(seconds=task.sla_seconds):
                self._sla_violations.append(task)
                self._log.warning(
                    "sla.violation", task_id=task.task_id, elapsed_seconds=elapsed.total_seconds()
                )

    def get_sla_violations(self) -> list[Task]:
        return list(self._sla_violations)


def _priority_value(p: TaskPriority) -> int:
    return {"low": 0, "normal": 1, "high": 2, "critical": 3}.get(p.value, 1)


__all__ = [
    "EnterpriseTaskQueue",
    "Task",
    "TaskPriority",
    "TaskStatus",
]
