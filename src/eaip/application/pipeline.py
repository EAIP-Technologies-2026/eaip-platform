"""StartupPipeline — ordered lifecycle phases for application startup.

The :class:`StartupPipeline` provides a structured startup sequence:

1. **PRE_BOOTSTRAP** — validate configuration, check connectivity, warm caches.
2. **BOOTSTRAP** — create kernel, register modules, wire DI.
3. **RUNTIME** — start the runtime kernel (starts all modules).
4. **POST_BOOTSTRAP** — publish "ready" events, start background workers.
5. **SHUTDOWN** — stop everything gracefully.

Each phase accepts sync or async hooks.  Hooks are executed in registration
order within a phase.  If a hook fails, the pipeline enters FAILED state and
rolls back already-executed phases in reverse order.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from eaip.exceptions.domain import LifecycleError
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    pass


class StartupPhase(StrEnum):
    """Discrete phases of the application startup pipeline."""

    CREATED = "created"
    PRE_BOOTSTRAP = "pre_bootstrap"
    BOOTSTRAP = "bootstrap"
    RUNTIME = "runtime"
    POST_BOOTSTRAP = "post_bootstrap"
    RUNNING = "running"
    SHUTDOWN = "shutdown"
    STOPPED = "stopped"
    FAILED = "failed"


PipelineHook = Callable[..., Any]


@dataclass(slots=True)
class _PipelineEntry:
    name: str
    fn: PipelineHook
    phase: StartupPhase


class StartupPipeline:
    """Ordered lifecycle pipeline for application startup and shutdown.

    The pipeline progresses through phases in a fixed order:

        CREATED → PRE_BOOTSTRAP → BOOTSTRAP → RUNTIME →
        POST_BOOTSTRAP → RUNNING

    On shutdown:

        RUNNING → SHUTDOWN → STOPPED

    If any phase hook raises, the pipeline enters FAILED and rolls back.

    Usage::

        pipeline = StartupPipeline()


        @pipeline.on("pre_bootstrap")
        async def validate_config(pipeline, ctx): ...


        @pipeline.on("post_bootstrap")
        def log_ready(pipeline, ctx): ...


        await pipeline.run(ctx)
        # pipeline.phase is now RUNNING
        ...
        await pipeline.shutdown()
    """

    def __init__(self) -> None:
        """Initialize the pipeline with default phase and empty state."""
        self._entries: list[_PipelineEntry] = []
        self._phase: StartupPhase = StartupPhase.CREATED
        self._started_at: datetime | None = None
        self._completed_phases: list[StartupPhase] = []
        self._log = get_logger("eaip.application.pipeline")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def phase(self) -> StartupPhase:
        """Return the current pipeline phase."""
        return self._phase

    @property
    def is_running(self) -> bool:
        """``True`` if the pipeline reached RUNNING phase."""
        return self._phase is StartupPhase.RUNNING

    @property
    def is_stopped(self) -> bool:
        """``True`` if the pipeline reached STOPPED phase."""
        return self._phase is StartupPhase.STOPPED

    @property
    def is_failed(self) -> bool:
        """``True`` if the pipeline entered FAILED phase."""
        return self._phase is StartupPhase.FAILED

    @property
    def started_at(self) -> datetime | None:
        """Return the timestamp when the pipeline started."""
        return self._started_at

    @property
    def completed_phases(self) -> list[StartupPhase]:
        """Return a copy of the completed phases list."""
        return list(self._completed_phases)

    @property
    def hook_count(self) -> int:
        """Return the number of registered hooks."""
        return len(self._entries)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def on(
        self,
        phase: str | StartupPhase,
        name: str | None = None,
    ) -> Callable[[PipelineHook], PipelineHook]:
        """Register a hook for the given *phase*.

        Can be used as a decorator::

            @pipeline.on("pre_bootstrap", name="validate_config")
            async def hook(pipeline, ctx): ...

        Or called directly::

            pipeline.register("pre_bootstrap", my_fn, name="my_fn")
        """
        resolved = StartupPhase(phase) if isinstance(phase, str) else phase

        def decorator(fn: PipelineHook) -> PipelineHook:
            hook_name: str = name if name is not None else fn.__name__
            self._entries.append(_PipelineEntry(name=hook_name, fn=fn, phase=resolved))
            return fn

        return decorator

    def register(
        self,
        phase: str | StartupPhase,
        fn: PipelineHook,
        *,
        name: str | None = None,
    ) -> None:
        """Register *fn* to run during *phase*."""
        resolved = StartupPhase(phase) if isinstance(phase, str) else phase
        hook_name: str = name if name is not None else str(getattr(fn, "__name__", "unknown"))
        self._entries.append(_PipelineEntry(name=hook_name, fn=fn, phase=resolved))

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def run(self, context: Any = None) -> None:
        """Execute the pipeline through all startup phases.

        Args:
            context: Optional context object passed to every hook.
        """
        if self._phase is not StartupPhase.CREATED:
            raise LifecycleError(
                f"cannot run pipeline in phase {self._phase}",
                context={"phase": str(self._phase)},
            )

        self._started_at = utc_now()
        phases = [
            StartupPhase.PRE_BOOTSTRAP,
            StartupPhase.BOOTSTRAP,
            StartupPhase.RUNTIME,
            StartupPhase.POST_BOOTSTRAP,
        ]

        try:
            for phase in phases:
                self._phase = phase
                await self._run_phase(phase, context)
                self._completed_phases.append(phase)

            self._phase = StartupPhase.RUNNING
            self._log.info("pipeline.running")
        except Exception as exc:
            self._phase = StartupPhase.FAILED
            self._log.error("pipeline.failed", error=repr(exc))
            await self._rollback()
            raise

    async def shutdown(self) -> None:
        """Execute the shutdown phase.

        Idempotent: calling :meth:`shutdown` after already stopped is safe.
        """
        if self._phase in {StartupPhase.CREATED, StartupPhase.STOPPED}:
            return
        if self._phase is StartupPhase.FAILED:
            await self._rollback()
            self._phase = StartupPhase.STOPPED
            self._log.info("pipeline.stopped")
            return

        self._phase = StartupPhase.SHUTDOWN
        self._log.info("pipeline.shutting_down")
        try:
            await self._run_phase(StartupPhase.SHUTDOWN, None)
        except Exception as exc:
            self._log.error("pipeline.shutdown_failed", error=repr(exc))
        finally:
            await self._rollback()
            self._phase = StartupPhase.STOPPED
            self._log.info("pipeline.stopped")

    async def __aenter__(self) -> StartupPipeline:
        """Enter async context: run the pipeline."""
        await self.run()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Exit async context: shut down the pipeline."""
        await self.shutdown()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _run_phase(self, phase: StartupPhase, context: Any) -> None:
        entries = [e for e in self._entries if e.phase is phase]
        if not entries:
            self._log.debug("pipeline.phase.no_hooks", phase=phase.value)
            return

        self._log.info("pipeline.phase.starting", phase=phase.value, hooks=len(entries))
        for entry in entries:
            try:
                result = entry.fn(self, context)
                if inspect.isawaitable(result):
                    await result
                self._log.debug("pipeline.hook.completed", phase=phase.value, hook=entry.name)
            except Exception as exc:
                self._log.error(
                    "pipeline.hook.failed",
                    phase=phase.value,
                    hook=entry.name,
                    error=repr(exc),
                )
                raise LifecycleError(
                    f"pipeline {phase.value} hook {entry.name!r} failed",
                    context={"phase": phase.value, "hook": entry.name},
                    cause=exc,
                ) from exc

    async def _rollback(self) -> None:
        """Run the SHUTDOWN phase if not already done, tolerating failures."""
        if (
            StartupPhase.SHUTDOWN not in self._completed_phases
            and self._phase is not StartupPhase.SHUTDOWN
        ):
            shutdown_entries = [e for e in self._entries if e.phase is StartupPhase.SHUTDOWN]
            for entry in reversed(shutdown_entries):
                try:
                    result = entry.fn(self, None)
                    if inspect.isawaitable(result):
                        await result
                except Exception as exc:
                    self._log.error(
                        "pipeline.rollback.failed",
                        hook=entry.name,
                        error=repr(exc),
                    )
        self._completed_phases.clear()


__all__ = [
    "PipelineHook",
    "StartupPhase",
    "StartupPipeline",
]
