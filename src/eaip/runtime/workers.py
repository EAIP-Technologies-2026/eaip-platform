"""BackgroundWorker — async worker pool for background task execution.

The :class:`BackgroundWorker` provides a bounded pool of async workers that
process tasks submitted via :meth:`enqueue`.  It integrates with the runtime
lifecycle through standard start/stop methods.

Usage::

    worker = BackgroundWorker(max_concurrency=4)
    worker.start()

    await worker.enqueue("greet", lambda: print("hello"))
    await worker.enqueue("fetch", fetch_data, url="https://...")

    await worker.stop()
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from eaip.exceptions.domain import WorkerPoolExhaustedError
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


@dataclass(frozen=True, slots=True)
class TaskResult:
    """Result of a background worker task execution.

    Attributes:
    ----------
    task_id:
        Unique identifier for this task execution.
    task_name:
        Human-readable name of the task.
    success:
        Whether the task completed without raising.
    duration_seconds:
        Wall-clock duration of task execution.
    error:
        The exception raised, if any.
    """

    task_id: str
    task_name: str
    success: bool
    duration_seconds: float
    error: BaseException | None = None


WorkFn = Callable[..., Awaitable[Any] | Any]


class BackgroundWorker:
    """Async worker pool for background tasks.

    Parameters
    ----------
    max_concurrency:
        Maximum number of tasks running simultaneously (default: 8).
    task_id_generator:
        Optional callable producing unique task IDs.  Defaults to a simple
        monotonic counter.
    name:
        Optional name for this worker pool (used in log messages).
    """

    def __init__(
        self,
        max_concurrency: int = 8,
        task_id_generator: Callable[[], str] | None = None,
        name: str = "default",
    ) -> None:
        """Initialize the worker pool with concurrency limit and optional name."""
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")

        self._max_concurrency = max_concurrency
        self._name = name
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._queue: asyncio.Queue[
            tuple[str, WorkFn, tuple[Any, ...], dict[str, Any]],
        ] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._results: asyncio.Queue[TaskResult] = asyncio.Queue()
        self._counter = 0
        self._id_generator = task_id_generator or self._default_id
        self._running = False
        self._log = get_logger(f"eaip.runtime.workers.{name}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the worker pool (idempotent).

        Spawns *max_concurrency* background worker coroutines that pull
        tasks from the internal queue.
        """
        if self._running:
            return
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker_loop(i))
            for i in range(self._max_concurrency)
        ]
        self._log.info(
            "worker.started",
            workers=self._max_concurrency,
            name=self._name,
        )

    async def stop(self, drain: bool = True) -> list[TaskResult]:
        """Stop the worker pool.

        Args:
            drain:
                If ``True``, wait for all pending tasks to complete before
                stopping.  If ``False``, cancel pending tasks immediately.

        Returns:
            A list of :class:`TaskResult` for tasks that completed (or failed).
        """
        if not self._running:
            return []

        self._running = False

        # Signal workers to stop by putting sentinel values.
        for _ in self._workers:
            await self._queue.put(("_STOP", _noop, (), {}))

        if not drain:
            # Cancel all queued tasks.
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break

        # Wait for all workers to finish.
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers.clear()

        # Collect remaining results.
        finished: list[TaskResult] = []
        while not self._results.empty():
            try:
                finished.append(self._results.get_nowait())
            except asyncio.QueueEmpty:
                break

        self._log.info("worker.stopped", tasks_completed=len(finished), name=self._name)
        return finished

    # ------------------------------------------------------------------
    # Task submission
    # ------------------------------------------------------------------

    async def enqueue(
        self,
        name: str,
        fn: WorkFn,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Enqueue a task for background execution.

        Args:
            name:
                Human-readable task name (used in logs and results).
            fn:
                The async (or sync) callable to execute.
            *args:
                Positional arguments passed to *fn*.
            **kwargs:
                Keyword arguments passed to *fn*.

        Returns:
            A unique task ID string.

        Raises:
            WorkerPoolExhaustedError: If the worker pool is not running.
        """
        if not self._running:
            raise WorkerPoolExhaustedError(
                f"worker pool '{self._name}' is not running",
                context={"worker_name": self._name, "task_name": name},
            )

        task_id = self._id_generator()
        await self._queue.put((task_id, fn, args, kwargs))
        self._log.debug("worker.enqueued", task_id=task_id, task_name=name)
        return task_id

    async def results(self) -> list[TaskResult]:
        """Drain and return all available task results (non-blocking)."""
        drained: list[TaskResult] = []
        while not self._results.empty():
            try:
                drained.append(self._results.get_nowait())
            except asyncio.QueueEmpty:
                break
        return drained

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _worker_loop(self, _index: int) -> None:
        """Background worker that pulls and processes tasks."""
        while self._running:
            try:
                task_id, fn, args, kwargs = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0,
                )
            except TimeoutError:
                continue

            if task_id == "_STOP":
                self._queue.task_done()
                break

            async with self._semaphore:
                result = await self._run_task(task_id, fn, args, kwargs)
                await self._results.put(result)
                self._queue.task_done()

    async def _run_task(
        self,
        task_id: str,
        fn: WorkFn,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> TaskResult:
        start = utc_now()
        task_name = getattr(fn, "__name__", "unknown")
        try:
            result = fn(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            elapsed = (utc_now() - start).total_seconds()
            self._log.debug(
                "worker.task.completed",
                task_id=task_id,
                task_name=task_name,
                duration=elapsed,
            )
            return TaskResult(
                task_id=task_id,
                task_name=task_name,
                success=True,
                duration_seconds=elapsed,
            )
        except BaseException as exc:
            elapsed = (utc_now() - start).total_seconds()
            self._log.warning(
                "worker.task.failed",
                task_id=task_id,
                task_name=task_name,
                duration=elapsed,
                error=repr(exc),
            )
            return TaskResult(
                task_id=task_id,
                task_name=task_name,
                success=False,
                duration_seconds=elapsed,
                error=exc,
            )

    @staticmethod
    def _default_id() -> str:
        return uuid.uuid4().hex[:12]

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> BackgroundWorker:
        """Enter async context: start the worker pool."""
        self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Exit async context: stop and drain the worker pool."""
        await self.stop(drain=True)


async def _noop() -> None:
    """Sentinel no-op function used internally."""
    return


__all__ = ["BackgroundWorker", "TaskResult", "WorkFn"]
