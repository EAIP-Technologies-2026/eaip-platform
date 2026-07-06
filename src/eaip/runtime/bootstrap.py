"""BootstrapManager — configurable lifecycle hooks around module startup.

The :class:`BootstrapManager` lets integration code register callbacks that
run **before** any module starts (``pre_start``) and **after** all modules
have started (``post_start``).

Typical uses
------------
* Pre-start: validate configuration, check external connectivity, warm caches.
* Post-start: publish "kernel ready" event, start background workers.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from eaip.exceptions.domain import LifecycleError
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.context import RuntimeContext
    from eaip.runtime.kernel import RuntimeKernel

BootstrapHook = Callable[..., Any]


@dataclass(slots=True)
class _BootstrapEntry:
    name: str
    fn: BootstrapHook


class BootstrapManager:
    """Registers and runs pre-start / post-start lifecycle hooks.

    Hooks are executed in registration order.  If a hook raises, the
    :class:`BootstrapManager` logs the error and re-raises it wrapped in a
    :class:`~eaip.exceptions.domain.LifecycleError`.
    """

    def __init__(self) -> None:
        self._pre_start: list[_BootstrapEntry] = []
        self._post_start: list[_BootstrapEntry] = []
        self._log = get_logger("eaip.runtime.bootstrap")

    def add_pre_start(self, name: str, fn: BootstrapHook) -> None:
        """Register ``fn`` to run before any module starts.

        The hook receives ``(kernel, ctx)`` where *kernel* is the
        :class:`RuntimeKernel` and *ctx* is the current
        :class:`~eaip.runtime.context.RuntimeContext`.
        """
        if not name:
            raise ValueError("bootstrap hook name must be non-empty")
        self._pre_start.append(_BootstrapEntry(name=name, fn=fn))

    def add_post_start(self, name: str, fn: BootstrapHook) -> None:
        """Register ``fn`` to run after all modules have started.

        Same signature as :meth:`add_pre_start`.
        """
        if not name:
            raise ValueError("bootstrap hook name must be non-empty")
        self._post_start.append(_BootstrapEntry(name=name, fn=fn))

    async def run_pre_start(
        self, kernel: RuntimeKernel, ctx: RuntimeContext
    ) -> None:
        """Execute all pre-start hooks in registration order."""
        await self._run("pre_start", self._pre_start, kernel, ctx)

    async def run_post_start(
        self, kernel: RuntimeKernel, ctx: RuntimeContext
    ) -> None:
        """Execute all post-start hooks in registration order."""
        await self._run("post_start", self._post_start, kernel, ctx)

    async def _run(
        self,
        phase: str,
        hooks: list[_BootstrapEntry],
        kernel: RuntimeKernel,
        ctx: RuntimeContext,
    ) -> None:
        for entry in hooks:
            try:
                result = entry.fn(kernel, ctx)
                if inspect.isawaitable(result):
                    await result
                self._log.debug(
                    "runtime.bootstrap.hook_completed",
                    phase=phase,
                    hook=entry.name,
                )
            except Exception as exc:
                self._log.error(
                    "runtime.bootstrap.hook_failed",
                    phase=phase,
                    hook=entry.name,
                    error=repr(exc),
                )
                raise LifecycleError(
                    f"bootstrap {phase} hook {entry.name!r} failed",
                    context={"phase": phase, "hook": entry.name},
                    cause=exc,
                ) from exc

    @property
    def pre_start_count(self) -> int:
        return len(self._pre_start)

    @property
    def post_start_count(self) -> int:
        return len(self._post_start)

    @property
    def hook_count(self) -> int:
        return len(self._pre_start) + len(self._post_start)


__all__ = ["BootstrapManager"]
