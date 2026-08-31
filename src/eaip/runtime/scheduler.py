"""Async task scheduler supporting one-shot and recurring tasks."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from eaip.logging.context import get_logger

TaskCoroutine = Callable[..., Awaitable[None]]


@dataclass
class TaskHandle:
    """Handle for a scheduled task, used for cancellation and inspection."""

    id: str
    name: str
    cancelled: bool = False


@dataclass
class _ScheduledTask:
    handle: TaskHandle
    coro_fn: TaskCoroutine
    interval_seconds: float | None
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    _task: asyncio.Task[None] | None = None


class Scheduler:
    """Async task scheduler for one-shot and recurring coroutine tasks."""

    def __init__(self) -> None:
        """Initialise an empty scheduler."""
        self._tasks: dict[str, _ScheduledTask] = {}
        self._running: bool = False
        self._log = get_logger("eaip.runtime.scheduler")

    @property
    def running(self) -> bool:
        """Return whether the scheduler is running."""
        return self._running

    @property
    def task_count(self) -> int:
        """Return the number of registered tasks."""
        return len(self._tasks)

    def every(
        self,
        name: str,
        seconds: float,
        coro_fn: TaskCoroutine,
        *args: Any,
        **kwargs: Any,
    ) -> TaskHandle:
        """Schedule a recurring task at *seconds* interval."""
        handle = TaskHandle(id=uuid4().hex, name=name)
        self._tasks[handle.id] = _ScheduledTask(
            handle=handle,
            coro_fn=coro_fn,
            interval_seconds=seconds,
            args=args,
            kwargs=kwargs,
        )
        return handle

    def once(
        self,
        name: str,
        delay_seconds: float,
        coro_fn: TaskCoroutine,
        *args: Any,
        **kwargs: Any,
    ) -> TaskHandle:
        """Schedule a one-shot task after *delay_seconds*."""
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        handle = TaskHandle(id=uuid4().hex, name=name)
        self._tasks[handle.id] = _ScheduledTask(
            handle=handle,
            coro_fn=coro_fn,
            interval_seconds=None,
            args=args,
            kwargs=kwargs,
        )
        return handle

    def cancel(self, handle_id: str) -> bool:
        """Cancel a scheduled task by handle ID. Returns True if found."""
        task = self._tasks.get(handle_id)
        if task is None:
            return False
        task.handle.cancelled = True
        if task._task is not None and not task._task.done():
            task._task.cancel()
        return True

    async def start(self) -> None:
        """Start executing all registered tasks."""
        self._running = True
        for task in list(self._tasks.values()):
            if task.interval_seconds is not None:
                task._task = asyncio.create_task(
                    self._run_recurring(task), name=f"scheduler:{task.handle.name}"
                )
            else:
                task._task = asyncio.create_task(
                    self._run_once(task), name=f"scheduler:{task.handle.name}"
                )

    async def stop(self) -> None:
        """Cancel all tasks and clear the schedule."""
        self._running = False
        for task in list(self._tasks.values()):
            if task._task is not None and not task._task.done():
                task._task.cancel()
        if self._tasks:
            pending = [
                t._task for t in self._tasks.values() if t._task is not None and not t._task.done()
            ]
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        self._tasks.clear()

    async def _run_recurring(self, task: _ScheduledTask) -> None:
        """Run a task on a loop until cancelled or stopped."""
        while self._running and not task.handle.cancelled:
            try:
                await task.coro_fn(*task.args, **task.kwargs)
            except asyncio.CancelledError:
                break
            except BaseException as exc:
                self._log.error(
                    "scheduler.task_failed",
                    task=task.handle.name,
                    error=repr(exc),
                )
            delay = task.interval_seconds or 0
            await asyncio.sleep(delay)

    async def _run_once(self, task: _ScheduledTask) -> None:
        """Run a task once after its delay, unless cancelled."""
        if task.handle.cancelled or not self._running:
            return
        try:
            await asyncio.sleep(task.interval_seconds if task.interval_seconds else 0)
        except asyncio.CancelledError:
            return
        try:
            await task.coro_fn(*task.args, **task.kwargs)
        except BaseException as exc:
            self._log.error(
                "scheduler.task_failed",
                task=task.handle.name,
                error=repr(exc),
            )
