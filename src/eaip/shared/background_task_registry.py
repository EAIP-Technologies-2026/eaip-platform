"""BackgroundTaskRegistry — track, manage, and gracefully shut down async tasks.

Replaces scattered ``asyncio.ensure_future()`` calls with a central registry
that supports cancellation, shutdown, and runtime statistics.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class TaskInfo:
    """Snapshot of a registered task's state."""

    id: str
    name: str
    created_at: float
    completed_at: float | None = None
    failed: bool = False
    error: str | None = None


class BackgroundTaskRegistry:
    """Central registry for background asyncio tasks.

    Usage::

        registry = BackgroundTaskRegistry()
        task = await registry.register("my-task", my_coroutine())
        # ...
        await registry.await_all(timeout=5.0)
    """

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._infos: dict[str, TaskInfo] = {}

    async def register(self, name: str, coro: asyncio.Task[Any] | None = None) -> asyncio.Task[Any]:
        """Register and track a background task.

        If *coro* is ``None``, a no-op task is created.  Returns the task.
        """
        task_id = f"{name}_{id(coro)}_{time.monotonic_ns()}"
        info = TaskInfo(id=task_id, name=name, created_at=time.monotonic())
        self._infos[task_id] = info

        async def _wrapped() -> None:
            try:
                if coro is not None:
                    await coro
            except BaseException as exc:
                info.failed = True
                info.error = str(exc)
                raise
            finally:
                info.completed_at = time.monotonic()

        task = asyncio.ensure_future(_wrapped())
        self._tasks[task_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(task_id, None))
        return task

    def register_fire_and_forget(self, name: str, coro: Any) -> asyncio.Task[Any] | None:
        """Fire a coroutine and track it as a background task.

        Returns the task handle (or ``None`` if scheduling failed).
        """
        try:
            return asyncio.ensure_future(self._register_and_run(name, coro))
        except Exception:
            return None

    async def _register_and_run(self, name: str, coro: Any) -> None:
        task_id = f"{name}_{id(coro)}_{time.monotonic_ns()}"
        info = TaskInfo(id=task_id, name=name, created_at=time.monotonic())
        self._infos[task_id] = info
        try:
            await coro
        except BaseException as exc:
            info.failed = True
            info.error = str(exc)
        finally:
            info.completed_at = time.monotonic()
            self._tasks.pop(task_id, None)

    async def await_all(self, timeout: float | None = None) -> None:
        """Wait for all registered tasks to complete.

        Args:
            timeout: Maximum seconds to wait. ``None`` means wait forever.
        """
        tasks = list(self._tasks.values())
        if not tasks:
            return
        await asyncio.wait(tasks, timeout=timeout)

    def cancel(self, task_id: str) -> bool:
        """Cancel a task by ID. Returns ``True`` if found."""
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.cancel()
        return True

    def cancel_all(self) -> int:
        """Cancel all tracked tasks. Returns the count cancelled."""
        count = len(self._tasks)
        for task in self._tasks.values():
            task.cancel()
        return count

    @property
    def active_count(self) -> int:
        return len(self._tasks)

    @property
    def total_count(self) -> int:
        return len(self._infos)

    @property
    def failed_count(self) -> int:
        return sum(1 for i in self._infos.values() if i.failed)

    def get_stats(self) -> dict[str, Any]:
        return {
            "active_count": self.active_count,
            "total_count": self.total_count,
            "failed_count": self.failed_count,
            "tasks": [{"id": k, "name": v.name, "failed": v.failed} for k, v in self._infos.items()],
        }


__all__ = ["BackgroundTaskRegistry", "TaskInfo"]
