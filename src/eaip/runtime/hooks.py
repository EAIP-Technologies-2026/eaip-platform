"""ObservabilityHooks — structured callbacks fired at runtime lifecycle boundaries.

:class:`ObservabilityHooks` provides a **synchronous, in-process** hook point
at well-defined kernel transitions.  It is not a replacement for the
:class:`~eaip.events.bus.EventBus` (which handles asynchronous domain events)
but rather a low-level, zero-cost call site used by the runtime host before
any async infrastructure is warm.

Design
------
- Hooks are registered as callables; failures are isolated (one failing hook
  must not block others).
- All hook parameters are plain Python objects — no Pydantic models — to keep
  latency near zero at critical startup paths.
- Hooks are called synchronously; async hooks belong on the EventBus instead.
- Extension hooks allow dynamic event types via :meth:`define` / :meth:`on` /
  :meth:`fire` for use by external code at integration points.

Typical uses
------------
- Performance instrumentation (start-time / stop-time measurements).
- Structured-log enrichment keyed on the exact phase transition.
- Test spies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from eaip.logging.context import get_logger

# Callable[..., None] is intentional: hook signatures evolve independently.
_Hook = Callable[..., None]


class ObservabilityHooks:
    """Registry of synchronous callbacks invoked at runtime boundaries.

    Usage::

        hooks = ObservabilityHooks()
        hooks.on_module_start(lambda module, ctx: print(f"starting {module}"))
        hooks.on_module_stop(lambda module, ctx: print(f"stopping {module}"))

    The host passes an :class:`ObservabilityHooks` instance to
    :class:`~eaip.runtime.host.RuntimeHost` at construction time.  If omitted,
    a no-op instance is used automatically.

    Extension hooks (``define`` / ``on`` / ``fire``) allow callers to create
    custom event types at runtime::

        hooks.define("my.event")
        hooks.on("my.event", lambda **kw: print(kw))
        hooks.fire("my.event", key="val")
    """

    def __init__(self) -> None:
        self._log = get_logger("eaip.runtime.hooks")
        self._on_host_starting: list[_Hook] = []
        self._on_host_running: list[_Hook] = []
        self._on_host_stopping: list[_Hook] = []
        self._on_host_stopped: list[_Hook] = []
        self._on_module_starting: list[_Hook] = []
        self._on_module_started: list[_Hook] = []
        self._on_module_stopping: list[_Hook] = []
        self._on_module_stopped: list[_Hook] = []
        self._on_module_error: list[_Hook] = []
        self._extension: dict[str, list[_Hook]] = {}

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------

    def on_host_starting(self, fn: _Hook) -> None:
        """Register a callback fired just before the host starts modules."""
        self._on_host_starting.append(fn)

    def on_host_running(self, fn: _Hook) -> None:
        """Register a callback fired once all modules are running."""
        self._on_host_running.append(fn)

    def on_host_stopping(self, fn: _Hook) -> None:
        """Register a callback fired when the host starts shutting down."""
        self._on_host_stopping.append(fn)

    def on_host_stopped(self, fn: _Hook) -> None:
        """Register a callback fired after all modules have stopped."""
        self._on_host_stopped.append(fn)

    def on_module_starting(self, fn: _Hook) -> None:
        """Register a callback fired just before a module's ``on_start`` runs."""
        self._on_module_starting.append(fn)

    def on_module_started(self, fn: _Hook) -> None:
        """Register a callback fired after a module's ``on_start`` completes."""
        self._on_module_started.append(fn)

    def on_module_stopping(self, fn: _Hook) -> None:
        """Register a callback fired just before a module's ``on_stop`` runs."""
        self._on_module_stopping.append(fn)

    def on_module_stopped(self, fn: _Hook) -> None:
        """Register a callback fired after a module's ``on_stop`` completes."""
        self._on_module_stopped.append(fn)

    def on_module_error(self, fn: _Hook) -> None:
        """Register a callback fired when a module raises during start or stop."""
        self._on_module_error.append(fn)

    # ------------------------------------------------------------------
    # Fire helpers (called by RuntimeHost)
    # ------------------------------------------------------------------

    def fire_host_starting(self, **kw: Any) -> None:
        """Fire all ``host_starting`` hooks."""
        self._fire(self._on_host_starting, **kw)

    def fire_host_running(self, **kw: Any) -> None:
        """Fire all ``host_running`` hooks."""
        self._fire(self._on_host_running, **kw)

    def fire_host_stopping(self, **kw: Any) -> None:
        """Fire all ``host_stopping`` hooks."""
        self._fire(self._on_host_stopping, **kw)

    def fire_host_stopped(self, **kw: Any) -> None:
        """Fire all ``host_stopped`` hooks."""
        self._fire(self._on_host_stopped, **kw)

    def fire_module_starting(self, **kw: Any) -> None:
        """Fire all ``module_starting`` hooks."""
        self._fire(self._on_module_starting, **kw)

    def fire_module_started(self, **kw: Any) -> None:
        """Fire all ``module_started`` hooks."""
        self._fire(self._on_module_started, **kw)

    def fire_module_stopping(self, **kw: Any) -> None:
        """Fire all ``module_stopping`` hooks."""
        self._fire(self._on_module_stopping, **kw)

    def fire_module_stopped(self, **kw: Any) -> None:
        """Fire all ``module_stopped`` hooks."""
        self._fire(self._on_module_stopped, **kw)

    def fire_module_error(self, **kw: Any) -> None:
        """Fire all ``module_error`` hooks."""
        self._fire(self._on_module_error, **kw)

    # ------------------------------------------------------------------
    # Extension hooks — dynamic event types for external callers
    # ------------------------------------------------------------------

    def define(self, event_name: str) -> None:
        """Register a new extension hook event type.

        Raises :class:`ValueError` if the event name is empty or already
        defined as a built-in hook type.
        """
        if not event_name:
            raise ValueError("extension event name must be non-empty")
        if self._is_builtin(event_name):
            raise ValueError(
                f"cannot define extension event {event_name!r}: conflicts with built-in hook"
            )
        if event_name not in self._extension:
            self._extension[event_name] = []

    def undefine(self, event_name: str) -> bool:
        """Remove an extension hook event type. Returns ``True`` if it existed."""
        removed = self._extension.pop(event_name, None) is not None
        if removed:
            self._log.debug("runtime.hook_undefined", event_name=event_name)
        return removed

    def on(self, event_name: str, fn: _Hook) -> None:
        """Register ``fn`` for the given extension or built-in event.

        For built-in events, delegates to the typed registration method.
        For extension events, the event must have been created via :meth:`define`.
        """
        if self._is_builtin(event_name):
            getattr(self, f"on_{event_name}")(fn)
            return
        if event_name not in self._extension:
            raise ValueError(
                f"unknown extension event {event_name!r}; call define() first"
            )
        self._extension[event_name].append(fn)

    def fire(self, event_name: str, **kw: Any) -> None:
        """Fire all hooks registered for the given event.

        For built-in events, delegates to the typed fire method.
        For extension events, the event must have been created via :meth:`define`.
        """
        if self._is_builtin(event_name):
            getattr(self, f"fire_{event_name}")(**kw)
            return
        if event_name not in self._extension:
            self._log.warning(
                "runtime.hook_unknown_event",
                event_name=event_name,
            )
            return
        self._fire(self._extension[event_name], **kw)

    def registered_events(self) -> list[str]:
        """Return all known event names (built-in + extension)."""
        builtin = [
            "host_starting",
            "host_running",
            "host_stopping",
            "host_stopped",
            "module_starting",
            "module_started",
            "module_stopping",
            "module_stopped",
            "module_error",
        ]
        return sorted(builtin + list(self._extension.keys()))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _is_builtin(event_name: str) -> bool:
        return event_name in {
            "host_starting",
            "host_running",
            "host_stopping",
            "host_stopped",
            "module_starting",
            "module_started",
            "module_stopping",
            "module_stopped",
            "module_error",
        }

    def _fire(self, hooks: list[_Hook], **kw: Any) -> None:
        for hook in hooks:
            try:
                hook(**kw)
            except Exception as exc:
                self._log.error(
                    "runtime.hook_error",
                    hook=getattr(hook, "__qualname__", repr(hook)),
                    error=repr(exc),
                )


__all__ = ["ObservabilityHooks"]
