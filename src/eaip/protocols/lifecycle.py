"""Lifecycle protocols implemented by components that need orchestrated
startup, shutdown, or resource disposal."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Startable(Protocol):
    """A component that performs synchronous startup work."""

    def start(self) -> None: ...


@runtime_checkable
class Stoppable(Protocol):
    """A component that performs synchronous shutdown work."""

    def stop(self) -> None: ...


@runtime_checkable
class Disposable(Protocol):
    """A component that needs to release resources at end of life."""

    def dispose(self) -> None: ...


@runtime_checkable
class AsyncStartable(Protocol):
    """Async counterpart of :class:`Startable`."""

    async def start(self) -> None: ...


@runtime_checkable
class AsyncStoppable(Protocol):
    """Async counterpart of :class:`Stoppable`."""

    async def stop(self) -> None: ...


@runtime_checkable
class AsyncDisposable(Protocol):
    """Async counterpart of :class:`Disposable`."""

    async def dispose(self) -> None: ...


__all__ = [
    "AsyncDisposable",
    "AsyncStartable",
    "AsyncStoppable",
    "Disposable",
    "Startable",
    "Stoppable",
]
