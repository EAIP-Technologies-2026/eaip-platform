"""Kernel-level domain events published by the CompositionRoot.

These events signal the top-level kernel lifecycle transitions and are
published on the platform :class:`~eaip.events.bus.EventBus`.
"""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class KernelEvent(DomainEvent):
    """Base class for all kernel lifecycle events."""

    event_type: ClassVar[str] = "eaip.runtime.kernel.event"


class KernelStarted(KernelEvent):
    """Published when the kernel has fully started (post-start hooks done)."""

    event_type: ClassVar[str] = "eaip.runtime.kernel.started"
    module_count: int = 0


class KernelStopped(KernelEvent):
    """Published after the kernel has fully stopped."""

    event_type: ClassVar[str] = "eaip.runtime.kernel.stopped"


__all__ = ["KernelEvent", "KernelStarted", "KernelStopped"]
