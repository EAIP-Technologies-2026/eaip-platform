"""Lifecycle manager — orchestrates startup & shutdown of registered hooks.

The manager guarantees:

* Hooks start in registration order.
* Hooks stop in **reverse** registration order.
* If startup fails partway through, already-started hooks are stopped (LIFO)
  before the failure is re-raised.
* Each hook may be sync or async; the manager normalises them.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeAlias

from eaip.exceptions.domain import LifecycleError
from eaip.lifecycle.phases import LifecyclePhase
from eaip.logging.context import get_logger

SyncHook: TypeAlias = Callable[[], None]
AsyncHook: TypeAlias = Callable[[], Awaitable[None]]
LifecycleHook: TypeAlias = SyncHook | AsyncHook


@dataclass(slots=True)
class _Entry:
    name: str
    start: LifecycleHook
    stop: LifecycleHook | None
    started: bool = False


class LifecycleManager:
    """Orchestrates ordered startup & reverse-ordered shutdown."""

    def __init__(self) -> None:
        self._entries: list[_Entry] = []
        self._phase: LifecyclePhase = LifecyclePhase.CREATED
        self._log = get_logger("eaip.lifecycle")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def phase(self) -> LifecyclePhase:
        return self._phase

    @property
    def hook_count(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def add(
        self,
        name: str,
        start: LifecycleHook,
        stop: LifecycleHook | None = None,
    ) -> None:
        """Register a lifecycle hook.

        Adding hooks is forbidden once the manager has started.
        """
        if self._phase is not LifecyclePhase.CREATED:
            raise LifecycleError(
                f"cannot add lifecycle hooks in phase {self._phase}",
                context={"phase": str(self._phase)},
            )
        if not name:
            raise ValueError("lifecycle hook name must be non-empty")
        self._entries.append(_Entry(name=name, start=start, stop=stop))

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Run every ``start`` hook in registration order."""
        if self._phase is not LifecyclePhase.CREATED:
            raise LifecycleError(
                f"cannot start lifecycle in phase {self._phase}",
                context={"phase": str(self._phase)},
            )
        self._phase = LifecyclePhase.STARTING
        self._log.info("lifecycle.starting", hooks=len(self._entries))

        for entry in self._entries:
            try:
                await self._invoke(entry.start)
                entry.started = True
                self._log.debug("lifecycle.hook_started", hook=entry.name)
            except BaseException as exc:
                self._phase = LifecyclePhase.FAILED
                self._log.error(
                    "lifecycle.start_failed",
                    hook=entry.name,
                    error=repr(exc),
                )
                await self._rollback()
                raise LifecycleError(
                    f"lifecycle hook {entry.name!r} failed during start",
                    context={"hook": entry.name},
                    cause=exc,
                ) from exc

        self._phase = LifecyclePhase.RUNNING
        self._log.info("lifecycle.running")

    async def stop(self) -> None:
        """Run every ``stop`` hook in reverse order. Idempotent for STOPPED."""
        if self._phase in {LifecyclePhase.STOPPED, LifecyclePhase.CREATED}:
            return
        if self._phase not in {LifecyclePhase.RUNNING, LifecyclePhase.FAILED}:
            raise LifecycleError(
                f"cannot stop lifecycle in phase {self._phase}",
                context={"phase": str(self._phase)},
            )
        self._phase = LifecyclePhase.STOPPING
        self._log.info("lifecycle.stopping")
        await self._rollback()
        self._phase = LifecyclePhase.STOPPED
        self._log.info("lifecycle.stopped")

    async def _rollback(self) -> None:
        for entry in reversed(self._entries):
            if not entry.started or entry.stop is None:
                continue
            try:
                await self._invoke(entry.stop)
            except BaseException as exc:
                self._log.error(
                    "lifecycle.stop_failed",
                    hook=entry.name,
                    error=repr(exc),
                )
            finally:
                entry.started = False

    @staticmethod
    async def _invoke(hook: LifecycleHook) -> None:
        result = hook()
        if inspect.isawaitable(result):
            await result


__all__ = ["LifecycleHook", "LifecycleManager"]
