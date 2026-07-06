"""Runtime domain events published on the platform EventBus.

All runtime events extend :class:`~eaip.events.event.DomainEvent`.  The bus
delivers them to any subscriber that has called
``platform.events.subscribe(SomeRuntimeEvent, handler)``.

Subscribers should treat these events as **informational** — they are
fire-and-collect, meaning individual handler failures do not block the
kernel.
"""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent

# ---------------------------------------------------------------------------
# Base event
# ---------------------------------------------------------------------------


class RuntimeEvent(DomainEvent):
    """Base class for all runtime kernel events."""

    event_type: ClassVar[str] = "eaip.runtime.event"


# ---------------------------------------------------------------------------
# Module lifecycle events
# ---------------------------------------------------------------------------


class ModuleRegistered(RuntimeEvent):
    """Published when a module is added to the loader's registry."""

    event_type: ClassVar[str] = "eaip.runtime.module.registered"
    module_name: str = ""


class ModuleStarted(RuntimeEvent):
    """Published after a module's :meth:`on_start` completes successfully."""

    event_type: ClassVar[str] = "eaip.runtime.module.started"
    module_name: str = ""


class ModuleStopped(RuntimeEvent):
    """Published after a module's :meth:`on_stop` completes."""

    event_type: ClassVar[str] = "eaip.runtime.module.stopped"
    module_name: str = ""


class ModuleStartFailed(RuntimeEvent):
    """Published when a module's :meth:`on_start` raises an exception."""

    event_type: ClassVar[str] = "eaip.runtime.module.start_failed"
    module_name: str = ""
    error: str = ""


class ModuleStopFailed(RuntimeEvent):
    """Published when a module's :meth:`on_stop` raises an exception."""

    event_type: ClassVar[str] = "eaip.runtime.module.stop_failed"
    module_name: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# Host lifecycle events
# ---------------------------------------------------------------------------


class RuntimeStarting(RuntimeEvent):
    """Published when the :class:`~eaip.runtime.host.RuntimeHost` begins startup."""

    event_type: ClassVar[str] = "eaip.runtime.host.starting"
    module_count: int = 0


class RuntimeRunning(RuntimeEvent):
    """Published when all modules have started and the host is fully running."""

    event_type: ClassVar[str] = "eaip.runtime.host.running"
    module_count: int = 0


class RuntimeStopping(RuntimeEvent):
    """Published when the host begins its graceful shutdown sequence."""

    event_type: ClassVar[str] = "eaip.runtime.host.stopping"


class RuntimeStopped(RuntimeEvent):
    """Published once all modules have stopped."""

    event_type: ClassVar[str] = "eaip.runtime.host.stopped"


__all__ = [
    "ModuleRegistered",
    "ModuleStartFailed",
    "ModuleStarted",
    "ModuleStopFailed",
    "ModuleStopped",
    "RuntimeEvent",
    "RuntimeRunning",
    "RuntimeStarting",
    "RuntimeStopped",
    "RuntimeStopping",
]
